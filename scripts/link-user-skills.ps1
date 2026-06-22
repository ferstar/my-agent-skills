param(
  [switch]$Force
)

$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$SkillsDir = Join-Path $RepoRoot "skills"
$TargetDir = if ($env:AGENTS_SKILLS_DIR) { $env:AGENTS_SKILLS_DIR } else { Join-Path $HOME ".agents\skills" }

New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null

function Normalize-Path([string]$Path) {
  $TrimChars = @([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar)
  return [IO.Path]::GetFullPath($Path).TrimEnd($TrimChars)
}

function Assert-UnderTargetDir([string]$Path) {
  $FullPath = Normalize-Path $Path
  $FullTargetDir = Normalize-Path $TargetDir
  if ($FullPath -ne $FullTargetDir -and -not $FullPath.StartsWith($FullTargetDir + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Refusing to remove path outside target dir: $Path"
  }
}

function Get-ReparseTarget([System.IO.FileSystemInfo]$Item) {
  if ($Item.Target -and $Item.Target.Count -gt 0) {
    return Normalize-Path $Item.Target[0]
  }
  if ($Item.LinkTarget) {
    return Normalize-Path $Item.LinkTarget
  }
  return $null
}

Get-ChildItem -Path $SkillsDir -Directory | ForEach-Object {
  $Skill = $_.FullName
  if (-not (Test-Path (Join-Path $Skill "SKILL.md"))) { return }

  $Name = $_.Name
  $Target = Join-Path $TargetDir $Name

  if (Test-Path $Target) {
    $Item = Get-Item $Target -Force
    $IsLink = [bool]($Item.Attributes -band [IO.FileAttributes]::ReparsePoint)
    if ($IsLink) {
      if ((Get-ReparseTarget $Item) -eq (Normalize-Path $Skill)) {
        Write-Host "ok $Target -> $Skill"
        return
      }
      Assert-UnderTargetDir $Target
      [IO.Directory]::Delete($Target, $false)
    } elseif ($Force) {
      Assert-UnderTargetDir $Target
      Remove-Item -LiteralPath $Target -Recurse -Force
    } else {
      Write-Warning "skip $Target exists; use -Force to replace"
      return
    }
  }

  New-Item -ItemType Junction -Path $Target -Target $Skill | Out-Null
  Write-Host "link $Target -> $Skill"
}
