$ErrorActionPreference = 'Stop'
$blenderExe = 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe'
if (-not (Test-Path -LiteralPath $blenderExe)) {
    throw "Blender 5.2 nije pronađen na očekivanoj putanji: $blenderExe"
}
& $blenderExe --background --python blender/build_zoo.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $blenderExe --background --python blender/validate_animals.py
exit $LASTEXITCODE
