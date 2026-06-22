param(
  [switch]$Force
)

$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$SkillsDir = Join-Path $RepoRoot "skills"
$TargetDir = if ($env:AGENTS_SKILLS_DIR) { $env:AGENTS_SKILLS_DIR } else { Join-Path $HOME ".agents\skills" }

New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null

Get-ChildItem -Path $SkillsDir -Directory | ForEach-Object {
  $Skill = $_.FullName
  if (-not (Test-Path (Join-Path $Skill "SKILL.md"))) { return }

  $Name = $_.Name
  $Target = Join-Path $TargetDir $Name

  if (Test-Path $Target) {
    $Item = Get-Item $Target -Force
    $IsLink = [bool]($Item.Attributes -band [IO.FileAttributes]::ReparsePoint)
    if ($IsLink) {
      if ((Resolve-Path $Target).Path -eq (Resolve-Path $Skill).Path) {
        Write-Host "ok $Target -> $Skill"
        return
      }
      Remove-Item $Target -Force
    } elseif ($Force) {
      Remove-Item $Target -Recurse -Force
    } else {
      Write-Warning "skip $Target exists; use -Force to replace"
      return
    }
  }

  New-Item -ItemType Junction -Path $Target -Target $Skill | Out-Null
  Write-Host "link $Target -> $Skill"
}
