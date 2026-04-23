@echo off
set /p script_path="Enter the full path to your Python script (.py): "
set /p batch_name="Enter the name for your batch file (e.g., run_my_script.bat): "

echo @echo off > "%batch_name%"
echo python "%script_path%" %%* >> "%batch_name%"
echo pause >> "%batch_name%"

echo.
echo Successfully created %batch_name%!
pause
