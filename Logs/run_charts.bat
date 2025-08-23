@echo off
echo Running Python script to plot CSV data...
python plot_fueldata.py 2> error.log
if %ERRORLEVEL% neq 0 (
    echo An error occurred. Check error.log for details.
    type error.log
)
pause