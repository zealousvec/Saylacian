# SPDX-License-Identifier: AGPL-3.0-or-later
param(
    [ValidateSet('doctor', 'scripts', 'report', 'train', 'evaluate')]
    [string]$Action = 'doctor',
    [string]$RunId,
    [int]$Target = 1000,
    [switch]$Resume,
    [string]$Workspace = (Join-Path $env:LOCALAPPDATA 'SaylacianResearchLab'),
    [string]$Python = (Join-Path $PSScriptRoot '..\.venv\Scripts\python.exe'),
    [string]$TrainingPython,
    [double]$Epochs = 1.0,
    [double]$LearningRate = 0.00001
)

$ErrorActionPreference = 'Stop'
if ($Action -in @('train', 'evaluate')) {
    if (-not $RunId) { throw 'Use -RunId to name the private training experiment.' }
    if (-not $TrainingPython) {
        $TrainingPython = Join-Path $Workspace 'runtime\training-venv\Scripts\python.exe'
    }
    $Python = $TrainingPython
}
if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
    throw "Python interpreter not found: $Python. Supply -Python or -TrainingPython."
}
$cli = Join-Path $PSScriptRoot 'local_translation_lab.py'
$arguments = @($cli, '--workspace', $Workspace)
switch ($Action) {
    'doctor' { $arguments += 'doctor' }
    'scripts' {
        if (-not $RunId) { throw 'Use -RunId so this run can be resumed.' }
        $arguments += @('transliteration-check', '--run-id', $RunId, '--target', "$Target")
        if ($Resume) { $arguments += '--resume' }
    }
    'report' {
        $arguments += @('report', '--json')
        if ($RunId) { $arguments += @('--run-id', $RunId) }
    }
    'train' {
        $arguments += @('train-multilingual-candidate', '--execute', '--experiment-id', $RunId,
            '--epochs', $Epochs.ToString([Globalization.CultureInfo]::InvariantCulture),
            '--learning-rate', $LearningRate.ToString([Globalization.CultureInfo]::InvariantCulture))
        if ($Resume) { $arguments += '--resume' }
    }
    'evaluate' {
        $evaluationId = $RunId + '-eval-' + [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ')
        $arguments += @('evaluate-multilingual-candidate', '--experiment-id', $RunId,
            '--run-id', $evaluationId)
    }
}
& $Python @arguments
exit $LASTEXITCODE
