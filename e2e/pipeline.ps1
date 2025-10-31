param(
    [string]$ImageTag = "algorithm-teacher:pipeline",
    [string]$ContainerName = "algo-pipeline",
    [int]$Port = 8000,
    [int]$TimeoutSec = 60
)

$ErrorActionPreference = "Stop"

function Write-Step($msg) {
    Write-Host ("[STEP] " + $msg)
}

function Assert-LastExit($msg) {
    if ($LASTEXITCODE -ne 0) {
        Write-Error $msg
        exit 1
    }
}

try {
    Write-Step "Building Docker image $ImageTag"
    docker build -f deployment/Dockerfile -t $ImageTag .
    Assert-LastExit "Docker build failed"

    Write-Step "Removing any existing container $ContainerName"
    docker rm -f $ContainerName 2>$null | Out-Null

    Write-Step "Starting container $ContainerName on port $Port"
    $runOutput = docker run -d --name $ContainerName -p "${Port}:8000" $ImageTag 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Docker run failed: $runOutput"
        exit 1
    }

    Write-Step "Waiting for service to become ready"
    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    $ready = $false
    while ((Get-Date) -lt $deadline) {
        try {
            $resp = Invoke-WebRequest -Uri "http://localhost:$Port/docs" -Method GET -TimeoutSec 5
            if ($resp.StatusCode -eq 200) { $ready = $true; break }
        } catch {
            Start-Sleep -Seconds 2
        }
    }
    if (-not $ready) { throw "Service did not become ready in $TimeoutSec sec" }

    Write-Step "Call POST /api/recommend"
    $body = @{ prompt = "Classify customer reviews by sentiment" } | ConvertTo-Json -Compress
    $resp = Invoke-RestMethod -Uri "http://localhost:$Port/api/recommend" -Method POST -ContentType "application/json" -Body $body
    if (-not $resp -or -not $resp.recommendations -or $resp.recommendations.Count -lt 1) {
        throw "Recommendation endpoint returned no items"
    }

    Write-Step "Call GET /api/reports/usage"
    $usage = Invoke-RestMethod -Uri "http://localhost:$Port/api/reports/usage" -Method GET
    if (-not $usage) {
        throw "Usage endpoint returned invalid response"
    }

    Write-Step "Call GET /metrics"
    $metrics = Invoke-WebRequest -Uri "http://localhost:$Port/metrics" -Method GET
    if ($metrics.StatusCode -ne 200) { throw "Metrics endpoint failed" }

    Write-Step "Pipeline succeeded"
    exit 0
} catch {
    Write-Error $_
    exit 1
} finally {
    Write-Step "Cleaning up container $ContainerName"
    docker rm -f $ContainerName 2>$null | Out-Null
}
