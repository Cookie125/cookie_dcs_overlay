This is a simple tool for logging player data and streaming it from a webserver to be used on a stream as an overlay with the added function of being able to output player telemetry to charts afterwards for added readability or for the purpose of reviewing tracks.
Note: This is my first time ever attempting such a project these scripts were made with the help of generative AI the solutions presented might not be ideal however since there was no open source offering I spent the time making and debugging it for you more code savvy people please be gentle im open to suggestions.
**I have also never wrote a read me so... yeah I will try my best

This system function as follows. A lua script must be loaded into the mission just like any other DCS script. This script will export all player data to a CSV file store in Saved Games/DCS/Logs. Note this CSV is overwritten once the mission is reloaded. For the primary function as an overlay this CSV is hosted on a simple Python Web server. This server is password protected and also has ip whitelisting to protect this data and the server. There are two htmls provided which contain the javascripting for the overlay and the ability to connect to the web server hosting the CSV. This is how the overlay functions. The other tool provided allows users to generate graphs of player data following a round in a match or while reviewing a track. More indepth instructions below.

Installation:
Prerequisite:
Latest Version of Python must be installed

Sanatize DCS:
Navigate to your DCS root directory than to Scripts/MissionScripting.lua
Open MissionScripting.lua and comment out each santize module to look as such:
  --sanitizeModule('os')
	--sanitizeModule('io')
	--sanitizeModule('lfs')
Once this is done save the file. Note this is overwritten when DCS is updated and must be re done in order for the Lua to function

LUA Install:
Load fuel-tracking.lua into the mission or track of choice. This can be done simply with "Do Script File" and selecting the script or the preffered way for easier updates would be instead to select "Do Script" and insert: 
"local scriptPath = lfs.writedir() .. [[scripts\fuel-tracking.lua]]
dofile(scriptPath)"

If you chose the latter method you must place fuel-tracking.lua into your Saved Games/DCS/Scripts folder

If you are primarily interested in reviewing tracks you can enable in game messages to show all data live during track replay simply open the fuel-tracking.lua script and change line#7 to the following: enableNotifications = true
There are other options that are able to be tweaked in the same section adjust as needed

Web Server and Chart Installation:
Simply place the provided logs folder into your Saved Games/DCS/Logs

Web Server Config:
Open port 5314 TCP or open overlay-server.py in a text editor of your choice go to Line #12 and set the port of your choice and open it.
If not already open the overlay-server.py in a text editor and you can now configure the server 
Line#15 allows you to set a username
Line#16 allows you to set a password
Line#18 is your IP whitelist you must whitelist any IP you want to allow in

Overlay Install:
Add fuel-overlay-blue.html and fuel-overlay-red.html to wherever you please on the streaming PC
Load each as a browser source on OBS

Overlay Config: 
Open both htmls in a text editor and navigate to line 188 it should look as follows: fetch('http://111.11.111.11:5314/server-fueldata.csv', {
Replace the IP with the host server's IP if the port configuration is different ensure you match the port
Navigate to line 190 which reads as follows: 'Authorization': 'Basic ' + btoa('admin:K7$mP9!xL2qJ4')
Replace admin with the usernamed configured on the server and following the username add the password. They should be seperated with a : as shown above. 
Save these changes and reload the overlay in OBS

Usage:
If all of the above steps were done correctly launch the desired mission or track.
If you wish to use the overlay lauch the Web Server using overlay-server_start.bat located in Saved Games/DCS/Logs
Reload the overlay on OBS it should now populate with each clients telemetry. 

Logging Functionality:
Also provided is a python script which generates graphs for easier dissemination of user telemetry. 
To use it you must open open a CMD and run the following once: pip install pandas matplotlib
Once this dependencey is installed you can simply click run_charts.bat found in Saved Games/DCS/Logs
***REMEMBER*** This Script only reads the CSV that is present in the logs folder this CSV is overwritten whenever the mission is reloaded. 
You have two options to preserve the data option 1 is to save the CSV file labeled server-fueldata.csv found is Saved Games/DCS/Logs elsewhere prior to reloading the mission or if the data is overwritten you can replay the server track on any client and a new server-fueldata.csv will be created. 
You should be able to take run_charts.bat and plot_fueldata.py and place them in a different folder of your choosing so you may review CSVs that are not the current one on the server. Simply place the CSV you would like to review in a folder with the other two and run the batch file. 

That should be the full setup reminder again this is all new to me but I have tested this system as much as I could and it runs well this ideally is a stop gap for something better however it has plenty of functionality in the current iteration. 
If you require help or have any questions contact me on discord: cookie125
