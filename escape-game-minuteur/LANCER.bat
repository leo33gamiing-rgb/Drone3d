@echo off
rem Lance la regie sans passer par l'icone du bureau.
start "" powershell -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "%~dp0outils\lanceur.ps1"
