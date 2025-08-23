-- DCS Mission Script: Enhanced Fuel, Ammo, and Missile Tracking System
-- Tracks fuel percentage, position, velocity, gun ammo, missile types (Active, Semi-Active, IR), coalition, and death status of all active aircraft and logs to CSV

-- Configuration
local fuelInterval = 5          -- seconds between fuel checks
local notificationInterval = 2  -- seconds between notifications
local notificationCounter = 0
local logFilePath = lfs.writedir() .. [[Logs\server-fueldata.csv]]
local telemetryTimeout = 30     -- seconds to consider a player dead if no telemetry
local lockFilePath = logFilePath .. ".lock"  -- Lock file to prevent concurrent access

-- Persistent table to track seen players across intervals
local seenPlayers = {}

-- Function to acquire a file lock
local function acquireLock()
    local lockFile = io.open(lockFilePath, "w")
    if not lockFile then
        env.error("Failed to create lock file: " .. lockFilePath)
        return false
    end
    lockFile:write(os.time())
    lockFile:flush()
    lockFile:close()
    return true
end

-- Function to release a file lock
local function releaseLock()
    os.remove(lockFilePath)
end

-- Function to get aircraft units
local function getAirUnits()
    local units = {}
    for _, coalitionId in pairs({coalition.side.RED, coalition.side.BLUE, coalition.side.NEUTRAL}) do
        local groups = coalition.getGroups(coalitionId, Group.Category.AIRPLANE)
        if groups then
            for _, group in ipairs(groups) do
                if group and group:isExist() then
                    local groupUnits = group:getUnits()
                    if groupUnits then
                        for _, unit in ipairs(groupUnits) do
                            if unit and unit:isExist() and unit:isActive() then
                                table.insert(units, unit)
                            end
                        end
                    end
                end
            end
        end
    end
    return units
end

-- Helper function to get position components
local function getPositionComponents(position)
    if not position then return 0, 0, 0 end
    return position.x or 0, position.y or 0, position.z or 0
end

-- Helper function to get velocity components
local function getVelocityComponents(velocity)
    if not velocity then return 0, 0, 0, 0 end
    local speed = math.sqrt((velocity.x or 0)^2 + (velocity.y or 0)^2 + (velocity.z or 0)^2)
    return velocity.x or 0, velocity.y or 0, velocity.z or 0, speed
end

-- Helper function to get gun ammo count
local function getGunAmmo(unit)
    local ammo = unit:getAmmo() or {}
    for _, item in ipairs(ammo) do
        if item.desc and item.desc.category == 0 and item.desc.typeName:match("shells") then -- Cannon shells
            return item.count or 0
        end
    end
    return 0
end

-- Helper function to get missile counts by type (Active, Semi-Active, IR)
local function getMissileTypes(unit)
    local ammo = unit:getAmmo() or {}
    local active = 0  -- Active radar (guidance 3)
    local semiActive = 0  -- Semi-active radar (guidance 1 or 4)
    local ir = 0  -- Infrared (guidance 2)
    for _, item in ipairs(ammo) do
        local desc = item.desc
        if desc and desc.category == 1 then -- All missiles
            local typeName = desc.typeName or ""
            env.info("Missile detected: " .. (typeName or "Unknown") .. ", Guidance: " .. (desc.guidance or "Unknown")) -- Debug log
            if desc.guidance == 3 or typeName:match("AIM%-120") or typeName:match("R%-77") then
                active = active + (item.count or 0)
            elseif (desc.guidance == 1 or desc.guidance == 4) or typeName:match("AIM%-7") or typeName:match("R%-27R") or typeName:match("R%-27ER") or typeName:match("P_27P") or typeName:match("P_27PE") then
                semiActive = semiActive + (item.count or 0)
            elseif desc.guidance == 2 or typeName:match("AIM%-9") or typeName:match("R%-73") or typeName:match("R%-27T") or typeName:match("R%-27ET") or typeName:match("P_27T") or typeName:match("P_27TE") then
                ir = ir + (item.count or 0)
            end
        end
    end
    -- Convert to string: "type:count;type:count"
    local missileStr = ""
    if active > 0 then missileStr = missileStr .. (missileStr ~= "" and ";" or "") .. "Active:" .. active else missileStr = missileStr .. (missileStr ~= "" and ";" or "") .. "Active:0" end
    if semiActive > 0 then missileStr = missileStr .. (missileStr ~= "" and ";" or "") .. "Semi-Active:" .. semiActive else missileStr = missileStr .. (missileStr ~= "" and ";" or "") .. "Semi-Active:0" end
    if ir > 0 then missileStr = missileStr .. (missileStr ~= "" and ";" or "") .. "IR:" .. ir else missileStr = missileStr .. (missileStr ~= "" and ";" or "") .. "IR:0" end
    return missileStr
end

-- Helper function to get coalition
local function getCoalition(unit)
    local group = unit:getGroup()
    if group then
        local coalitionId = group:getCoalition()
        if coalitionId == coalition.side.BLUE then return "Blue"
        elseif coalitionId == coalition.side.RED then return "Red"
        else return "Neutral" end
    end
    return "Unknown"
end

-- Main tracking function
local function checkFuel()
    notificationCounter = notificationCounter + fuelInterval
    local seconds = timer.getTime()
    local hours = math.floor(seconds / 3600)
    local minutes = math.floor((seconds % 3600) / 60)
    local secs = math.floor(seconds % 60)
    local currentTime = string.format("%02d:%02d:%02d", hours, minutes, secs)
    local unitArray = getAirUnits()
    local notificationString = "Current Fuel, Ammo, and Missile Status:\n"
    local humanFound = false
    local seenPlayersThisRun = {}

    for _, unit in ipairs(unitArray) do
        local fuel = unit:getFuel() or 0
        local playername = unit:getPlayerName()
        local unittype = unit:getTypeName()
        local gunAmmo = getGunAmmo(unit)
        local missileStr = getMissileTypes(unit)
        local position = unit:getPosition() and unit:getPosition().p
        local velocity = unit:getVelocity()
        local posX, posY, posZ = getPositionComponents(position)
        local velX, velY, velZ, speed = getVelocityComponents(velocity)
        local coalition = getCoalition(unit)
        local status = "Alive"

        if playername then
            seenPlayersThisRun[playername] = true
            -- Reset status to Alive if player reappears, and update telemetry
            if seenPlayers[playername] and seenPlayers[playername].status == "Dead" then
                seenPlayers[playername].status = "Alive"
                env.info("Player " .. playername .. " respawned, status reset to Alive")
            end
            seenPlayers[playername] = {
                time = currentTime,
                fuelPercent = string.format("%.1f", fuel * 100),
                unittype = unittype,
                gunAmmo = gunAmmo,
                missileStr = missileStr,
                posX = posX, posY = posY, posZ = posZ,
                velX = velX, velY = velY, velZ = velZ, speed = speed,
                coalition = coalition,
                status = status,
                lastSeen = timer.getTime() -- Update last seen time
            }
            -- Acquire lock before writing
            if acquireLock() then
                local file = io.open(logFilePath, "a")
                if file then
                    local logline = string.format("%s,%s,%s,%s,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%s,%s,%s,%s",
                        currentTime, playername, unittype, seenPlayers[playername].fuelPercent, posX, posY, posZ, velX, velY, velZ, speed, gunAmmo, missileStr, coalition, status)
                    file:write(logline .. "\n")
                    file:flush() -- Ensure data is written
                    file:close()
                else
                    env.error("Failed to open log file: " .. logFilePath)
                end
                releaseLock()
            else
                env.warning("Failed to acquire lock, skipping write for " .. playername)
            end

            humanFound = true
            notificationString = notificationString ..
                string.format("%s (%s): %s%% fuel, %s rounds, Missiles: %s, Coalition: %s, Status: %s\n", 
                    playername, unittype, seenPlayers[playername].fuelPercent, gunAmmo, missileStr, coalition, status)
        end
    end

    -- Check for players who disappeared or timed out with lock
    if acquireLock() then
        for playername, data in pairs(seenPlayers) do
            local currentTimeSeconds = timer.getTime()
            if not seenPlayersThisRun[playername] and data.status ~= "Dead" then
                -- Mark as Dead if player is no longer in a slot
                local file = io.open(logFilePath, "a")
                if file then
                    local logline = string.format("%s,%s,%s,%s,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%s,%s,%s,Dead",
                        currentTime, playername, data.unittype, data.fuelPercent, data.posX, data.posY, data.posZ, data.velX, data.velY, data.velZ, data.speed, data.gunAmmo, data.missileStr, data.coalition)
                    file:write(logline .. "\n")
                    file:flush()
                    file:close()
                    data.status = "Dead"
                    env.info("Player " .. playername .. " marked Dead due to deslot")
                end
            elseif data.status == "Alive" and (currentTimeSeconds - (data.lastSeen or 0)) >= telemetryTimeout then
                -- Mark as Dead if no telemetry for 30 seconds
                local file = io.open(logFilePath, "a")
                if file then
                    local logline = string.format("%s,%s,%s,%s,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%s,%s,%s,Dead",
                        currentTime, playername, data.unittype, data.fuelPercent, data.posX, data.posY, data.posZ, data.velX, data.velY, data.velZ, data.speed, data.gunAmmo, data.missileStr, data.coalition)
                    file:write(logline .. "\n")
                    file:flush()
                    file:close()
                    data.status = "Dead"
                    env.info("Player " .. playername .. " marked Dead due to telemetry timeout")
                end
            end
        end
        releaseLock()
    else
        env.warning("Failed to acquire lock for dead player check")
    end

    -- Show notification if interval reached and humans present
    if notificationCounter >= notificationInterval then
        notificationCounter = 0
        if humanFound then
            trigger.action.outText(notificationString, 30, true)
        end
    end

    -- Schedule next check
    timer.scheduleFunction(checkFuel, {}, timer.getTime() + fuelInterval)
end

-- Initialize CSV file with lock
local function initializeCSV()
    if acquireLock() then
        local file = io.open(logFilePath, "w")
        if file then
            file:write("Time,Player,Aircraft,Fuel_Percent,Pos_X,Pos_Y,Pos_Z,Vel_X,Vel_Y,Vel_Z,Speed,Gun_Ammo,Missile_Types,Coalition,Status\n")
            file:close()
            env.info("CSV file initialized with headers at: " .. logFilePath)
        else
            env.error("Failed to initialize CSV file at: " .. logFilePath)
        end
        releaseLock()
    else
        env.error("Failed to acquire lock for CSV initialization")
    end
end

-- Start the script
initializeCSV()
timer.scheduleFunction(checkFuel, {}, timer.getTime() + fuelInterval)
env.info("Enhanced fuel, ammo, and missile tracking script started. Interval: " .. fuelInterval .. "s")