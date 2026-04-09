@echo off
REM ========================================
REM Script pour vider le cache des navigateurs
REM Windows - Edge et Chrome
REM ========================================

echo ========================================
echo NETTOYAGE DU CACHE DES NAVIGATEURS
echo ========================================
echo.

REM Fermer les navigateurs
echo [1/4] Fermeture des navigateurs...
taskkill /F /IM chrome.exe 2>nul
taskkill /F /IM msedge.exe 2>nul
timeout /t 2 /nobreak >nul
echo      OK - Navigateurs fermes
echo.

REM Nettoyer le cache Chrome
echo [2/4] Nettoyage du cache Chrome...
set CHROME_CACHE=%LOCALAPPDATA%\Google\Chrome\User Data\Default\Cache
set CHROME_CACHE2=%LOCALAPPDATA%\Google\Chrome\User Data\Default\Code Cache
if exist "%CHROME_CACHE%" (
    rd /s /q "%CHROME_CACHE%" 2>nul
    echo      OK - Cache Chrome nettoye
) else (
    echo      Chrome non trouve ou deja nettoye
)
if exist "%CHROME_CACHE2%" (
    rd /s /q "%CHROME_CACHE2%" 2>nul
)
echo.

REM Nettoyer le cache Edge
echo [3/4] Nettoyage du cache Edge...
set EDGE_CACHE=%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Cache
set EDGE_CACHE2=%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Code Cache
if exist "%EDGE_CACHE%" (
    rd /s /q "%EDGE_CACHE%" 2>nul
    echo      OK - Cache Edge nettoye
) else (
    echo      Edge non trouve ou deja nettoye
)
if exist "%EDGE_CACHE2%" (
    rd /s /q "%EDGE_CACHE2%" 2>nul
)
echo.

REM Nettoyer les fichiers temporaires
echo [4/4] Nettoyage des fichiers temporaires...
del /q /f /s "%TEMP%\*" 2>nul
rd /s /q "%TEMP%" 2>nul
mkdir "%TEMP%"
echo      OK - Fichiers temporaires nettoyes
echo.

echo ========================================
echo NETTOYAGE TERMINE !
echo ========================================
echo.
echo Vous pouvez maintenant:
echo 1. Ouvrir Edge ou Chrome en mode navigation privee
echo 2. Acceder a: https://martialcomp.com/fr/competitions/club/competitions/management/
echo.
echo Appuyez sur une touche pour fermer...
pause >nul
