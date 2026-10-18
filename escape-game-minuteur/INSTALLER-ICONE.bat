@echo off
rem Cree l'icone "Escape Game - Minuteur" sur le bureau.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0outils\lanceur.ps1" -CreerIcone
if errorlevel 1 echo. & echo   Echec : voir le message ci-dessus.
pause
