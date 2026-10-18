param(
    [string]$Root = (Join-Path $PSScriptRoot "extracted"),
    [string]$MemberPath = "*"
)

$ErrorActionPreference = "Stop"

function Get-LowerSha256([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

$results = @()

Get-ChildItem -LiteralPath $Root -Directory | Sort-Object Name | ForEach-Object {
    $bundleDirectory = $_.FullName
    $manifestPath = Join-Path $bundleDirectory "bundle_manifest.json"
    $manifest = Get-Content -Raw -LiteralPath $manifestPath | ConvertFrom-Json

    foreach ($member in $manifest.members) {
        if ($member.path -notlike $MemberPath) {
            continue
        }
        # PowerShell variable names are case-insensitive. Keep this local name
        # distinct from the $MemberPath filter parameter so the first member
        # cannot overwrite the pattern used for the remaining files.
        $resolvedMemberPath = Join-Path $bundleDirectory $member.path
        $item = Get-Item -LiteralPath $resolvedMemberPath
        $hash = Get-LowerSha256 $resolvedMemberPath

        if ($item.Length -ne [long]$member.bytes) {
            throw "Byte-size mismatch: $($member.path)"
        }
        if ($hash -ne $member.sha256) {
            throw "SHA-256 mismatch: $($member.path)"
        }

        if ($member.kind -eq "documentation") {
            continue
        }

        $lineCount = 0
        $queryCount = 0
        $currentQid = $null
        $expectedRank = 1
        $currentDocs = [System.Collections.Generic.HashSet[string]]::new()

        foreach ($line in [System.IO.File]::ReadLines($resolvedMemberPath)) {
            $lineCount += 1
            $fields = $line.Split("`t")
            if ($fields.Count -ne 6) {
                throw "Expected six TREC fields in $($member.path), line $lineCount"
            }

            $qid = $fields[0]
            $docid = $fields[2]
            $rank = 0
            if (-not [int]::TryParse($fields[3], [ref]$rank)) {
                throw "Invalid rank in $($member.path), line $lineCount"
            }

            if ($qid -ne $currentQid) {
                if ($null -ne $currentQid -and $expectedRank -ne ([int]$member.max_depth + 1)) {
                    throw "Depth mismatch for qid $currentQid in $($member.path)"
                }
                $currentQid = $qid
                $queryCount += 1
                $expectedRank = 1
                $currentDocs.Clear()
            }

            if ($rank -ne $expectedRank) {
                throw "Expected rank $expectedRank for qid $qid in $($member.path), found $rank"
            }
            if (-not $currentDocs.Add($docid)) {
                throw "Duplicate document for qid $qid in $($member.path)"
            }
            $expectedRank += 1
        }

        if ($null -ne $currentQid -and $expectedRank -ne ([int]$member.max_depth + 1)) {
            throw "Depth mismatch for qid $currentQid in $($member.path)"
        }

        if ($lineCount -ne [long]$member.row_count) {
            throw "Row-count mismatch: $($member.path)"
        }
        if ($queryCount -ne [int]$member.query_count) {
            throw "Query-count mismatch: $($member.path)"
        }

        $results += [pscustomobject]@{
            ArtifactId = $manifest.artifact_id
            Path = $member.path
            Bytes = $item.Length
            SHA256 = $hash
            Rows = $lineCount
            Queries = $queryCount
            Depth = [int]$member.max_depth
            Status = "PASS"
        }
        Write-Output "PASS $($manifest.artifact_id) $($member.path): $lineCount rows, $queryCount queries, depth $($member.max_depth)"
    }
}

$results | Format-Table -AutoSize
Write-Output "Validated $($results.Count) ranked-run files."
