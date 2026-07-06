[CmdletBinding()]
param(
    [string]$DownloadsPath = (Join-Path $HOME 'Downloads'),
    [int]$Limit = 5,
    [int]$RecentHours = 168,
    [string]$NameContains = ''
)

$limitValue = [Math]::Max(1, $Limit)
$hoursValue = [Math]::Max(1, [Math]::Abs($RecentHours))
$cutoff = (Get-Date).AddHours(-$hoursValue)

if (-not (Test-Path -LiteralPath $DownloadsPath -PathType Container)) {
    '[]'
    exit 0
}

$files = Get-ChildItem -LiteralPath $DownloadsPath -Filter '*.png' -File -ErrorAction SilentlyContinue |
    Where-Object {
        $_.LastWriteTime -ge $cutoff -and
        ([string]::IsNullOrWhiteSpace($NameContains) -or $_.Name -like "*$NameContains*")
    } |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First $limitValue |
    ForEach-Object {
        [pscustomobject]@{
            name = $_.Name
            path = $_.FullName
            lastWriteTime = $_.LastWriteTime.ToString('s')
            sizeBytes = $_.Length
        }
    }

$fileArray = @($files)

if ($fileArray.Count -eq 0) {
    '[]'
} else {
    '[' + (($fileArray | ForEach-Object { $_ | ConvertTo-Json -Compress }) -join ',') + ']'
}
