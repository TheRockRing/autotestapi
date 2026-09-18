@echo off
cd /d "%~dp0"
call .venv\Scripts\activate.bat

behave features/token.feature
if errorlevel 1 exit /b 1

behave "features/PST/Xsell[Real]/lead_create.feature"
