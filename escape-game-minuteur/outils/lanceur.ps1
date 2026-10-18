# Lance la regie de l'escape game dans une fenetre dediee (Edge ou Chrome).
#   -CreerIcone  : cree l'icone "Escape Game - Minuteur" sur le bureau.
#   -MettreAJour : telecharge la derniere version de l'application et remplace les fichiers.
param([switch]$CreerIcone, [switch]$MettreAJour)
$ErrorActionPreference = 'Stop'

$dossier = Split-Path -Parent $PSScriptRoot
$page    = Join-Path $dossier 'index.html'
$icone   = Join-Path $PSScriptRoot 'icone.ico'
$profil  = Join-Path $env:LOCALAPPDATA 'EscapeGameMinuteur'
$urlMaj  = 'https://codeload.github.com/leo33gamiing-rgb/Drone3d/zip/refs/heads/claude/stoic-noether-n85a6g'

if ($MettreAJour) {
    $zip = Join-Path $env:TEMP 'escape-game-maj.zip'
    $tmp = Join-Path $env:TEMP 'escape-game-maj'
    Write-Host ''
    Write-Host '  Téléchargement de la dernière version...'
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri $urlMaj -OutFile $zip -UseBasicParsing
    if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force }
    Expand-Archive -Path $zip -DestinationPath $tmp -Force
    $source = Get-ChildItem $tmp -Directory -Recurse -Filter 'escape-game-minuteur' | Select-Object -First 1
    if (-not $source) { throw "Le dossier de l'application est introuvable dans le téléchargement." }
    # Copie par-dessus l'ancienne version (sons importés et réglages sont gardés dans le navigateur).
    robocopy $source.FullName $dossier /E /XF METTRE-A-JOUR.bat /NFL /NDL /NJH /NJS /NP | Out-Null
    if ($LASTEXITCODE -ge 8) { throw "La copie des fichiers a échoué (code $LASTEXITCODE)." }
    Remove-Item $zip, $tmp -Recurse -Force
    Write-Host '  Mise à jour terminée. Relancez la régie avec l''icône du bureau.' -ForegroundColor Green
    Write-Host ''
    return
}

$navigateur = @(
    "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe",
    "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe",
    "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
    "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
    "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $navigateur) { throw 'Microsoft Edge ou Google Chrome est introuvable sur ce PC.' }

# Profil dedie + options : son autorise sans clic, minuteur jamais ralenti en arriere-plan.
$arguments = @(
    "--app=`"$(([Uri]$page).AbsoluteUri)`""
    "--user-data-dir=`"$profil`""
    '--autoplay-policy=no-user-gesture-required'
    '--disable-background-timer-throttling'
    '--disable-renderer-backgrounding'
    '--disable-backgrounding-occluded-windows'
    '--disable-features=IntensiveWakeUpThrottling'
    '--no-first-run'
    '--no-default-browser-check'
    '--window-size=1400,900'
) -join ' '

if ($CreerIcone) {
    $raccourci = Join-Path ([Environment]::GetFolderPath('Desktop')) 'Escape Game - Minuteur.lnk'
    $lnk = (New-Object -ComObject WScript.Shell).CreateShortcut($raccourci)
    $lnk.TargetPath = $navigateur
    $lnk.Arguments = $arguments
    $lnk.WorkingDirectory = $dossier
    $lnk.IconLocation = "$icone,0"
    $lnk.Description = "Minuteur et régie sonore de l'escape game"
    $lnk.Save()
    Write-Host ''
    Write-Host "  Icône créée sur le bureau : $raccourci" -ForegroundColor Green
    Write-Host '  Double-cliquez dessus pour lancer la régie.'
    Write-Host ''
} else {
    Start-Process -FilePath $navigateur -ArgumentList $arguments
}
