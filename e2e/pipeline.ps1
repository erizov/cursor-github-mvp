param(
    [string]$ImageTag = "",
    [string]$ContainerName = "algo-pipeline",
    [int]$Port = 8000,
    [int]$TimeoutSec = 60,
    [string]$Backend = "inmemory",
    [string]$MongoContainer = "algo-mongo-pipeline"
)

$ErrorActionPreference = "Stop"

# Generate timestamped image name if not provided: alg-teach-backend-yyyymmdd-hhmmss
if ([string]::IsNullOrEmpty($ImageTag)) {
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $ImageTag = "alg-teach-$Backend-$timestamp"
}

# Validate backend
$validBackends = @("inmemory", "mongodb", "sqlite")
if ($validBackends -notcontains $Backend) {
    Write-Error "Invalid backend: $Backend. Must be one of: $($validBackends -join ', ')"
    exit 1
}

# Set Dockerfile path based on backend
$dockerfileMap = @{
    "inmemory" = "deployment/Dockerfile.inmemory"
    "mongodb" = "deployment/Dockerfile.mongodb"
    "sqlite" = "deployment/Dockerfile.sqlite"
}
$DockerfilePath = $dockerfileMap[$Backend]

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
    # Start MongoDB if needed
    if ($Backend -eq "mongodb") {
        Write-Step "Starting MongoDB container $MongoContainer"
        docker rm -f $MongoContainer 2>$null | Out-Null
        $mongoNetwork = "algo-network-pipeline"
        docker network create $mongoNetwork 2>$null | Out-Null
        
        $mongoRun = docker run -d --name $MongoContainer --network $mongoNetwork mongo:7 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Error "MongoDB container start failed: $mongoRun"
            exit 1
        }
        Start-Sleep -Seconds 3
    }
    
    Write-Step "Building Docker image $ImageTag from $DockerfilePath"
    docker build -f $DockerfilePath -t $ImageTag .
    Assert-LastExit "Docker build failed"

    Write-Step "Removing any existing container $ContainerName"
    docker rm -f $ContainerName 2>$null | Out-Null

    # Prepare docker run command
    $dockerRunArgs = @(
        "run", "-d",
        "--name", $ContainerName,
        "-p", "${Port}:8000"
    )
    
    if ($Backend -eq "mongodb") {
        $dockerRunArgs += @(
            "--network", $mongoNetwork,
            "-e", "MONGODB_URI=mongodb://$MongoContainer:27017"
        )
    }
    
    $dockerRunArgs += @($ImageTag)
    
    Write-Step "Starting container $ContainerName on port $Port (backend: $Backend)"
    $runOutput = docker $dockerRunArgs 2>&1
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
    
    if ($Backend -eq "mongodb") {
        Write-Step "Cleaning up MongoDB container $MongoContainer"
        docker rm -f $MongoContainer 2>$null | Out-Null
        docker network rm algo-network-pipeline 2>$null | Out-Null
    }
}
