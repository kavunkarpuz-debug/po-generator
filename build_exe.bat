@echo off
cd /d "%~dp0"
echo PO Generator EXE Olusturuluyor...
echo Calisma dizini: %cd%
echo.
echo Lutfen bekleyin, bu islem 1-2 dakika surebilir.
pyinstaller --noconsole --onefile --add-data "core;core" --add-data "gui;gui" --name "PO_Generator" main.pyw
echo.
echo Islem tamamlandi! EXE dosyaniz "dist" klasorunun icindedir.
pause
