@echo off
rem Telecharge la derniere version de l'application et remplace les fichiers.
rem Fermez la regie avant de lancer la mise a jour.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0outils\lanceur.ps1" -MettreAJour
if errorlevel 1 echo. & echo   Echec : voir le message ci-dessus.
pause
