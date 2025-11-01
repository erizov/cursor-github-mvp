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
$validBackends = @("inmemory", "mongodb", "postgres", "memcached", "neo4j", "cassandra")
if ($validBackends -notcontains $Backend) {
    Write-Error "Invalid backend: $Backend. Must be one of: $($validBackends -join ', ')"
    exit 1
}

# Set Dockerfile path based on backend
$dockerfileMap = @{
    "inmemory" = "deployment/Dockerfile.inmemory"
    "mongodb" = "deployment/Dockerfile.mongodb"
    "postgres" = "deployment/Dockerfile.postgres"
    "memcached" = "deployment/Dockerfile.memcached"
    "neo4j" = "deployment/Dockerfile.neo4j"
    "cassandra" = "deployment/Dockerfile.cassandra"
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
    # Start database containers if needed
    $dbNetwork = "algo-network-pipeline"
    docker network create $dbNetwork 2>$null | Out-Null
    
    if ($Backend -eq "mongodb") {
        Write-Step "Starting MongoDB container"
        docker rm -f $MongoContainer 2>$null | Out-Null
        docker run -d --name $MongoContainer --network $dbNetwork mongo:7 2>&1 | Out-Null
        Assert-LastExit "MongoDB container start failed"
        Start-Sleep -Seconds 3
    }
    elseif ($Backend -eq "postgres") {
        Write-Step "Starting PostgreSQL container"
        docker rm -f algo-postgres-pipeline 2>$null | Out-Null
        docker run -d --name algo-postgres-pipeline --network $dbNetwork `
            -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=ai_algo_teacher `
            postgres:16-alpine 2>&1 | Out-Null
        Assert-LastExit "PostgreSQL container start failed"
        Start-Sleep -Seconds 5
    }
    elseif ($Backend -eq "memcached") {
        Write-Step "Starting Memcached container"
        docker rm -f algo-memcached-pipeline 2>$null | Out-Null
        docker run -d --name algo-memcached-pipeline --network $dbNetwork memcached:1.6-alpine 2>&1 | Out-Null
        Assert-LastExit "Memcached container start failed"
        Start-Sleep -Seconds 2
    }
    elseif ($Backend -eq "neo4j") {
        Write-Step "Starting Neo4j container"
        docker rm -f algo-neo4j-pipeline 2>$null | Out-Null
        docker run -d --name algo-neo4j-pipeline --network $dbNetwork `
            -e NEO4J_AUTH=neo4j/password neo4j:5-community 2>&1 | Out-Null
        Assert-LastExit "Neo4j container start failed"
        Start-Sleep -Seconds 10
    }
    elseif ($Backend -eq "cassandra") {
        Write-Step "Starting Cassandra container"
        docker rm -f algo-cassandra-pipeline 2>$null | Out-Null
        docker run -d --name algo-cassandra-pipeline --network $dbNetwork cassandra:5 2>&1 | Out-Null
        Assert-LastExit "Cassandra container start failed"
        Start-Sleep -Seconds 15
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
        "-p", "${Port}:8000",
        "--network", $dbNetwork
    )
    
    # Set backend-specific environment variables
    if ($Backend -eq "mongodb") {
        $dockerRunArgs += @("-e", "MONGODB_URI=mongodb://$MongoContainer:27017")
    }
    elseif ($Backend -eq "postgres") {
        $dockerRunArgs += @("-e", "POSTGRES_URI=postgresql://postgres:postgres@algo-postgres-pipeline:5432/ai_algo_teacher")
    }
    elseif ($Backend -eq "memcached") {
        $dockerRunArgs += @("-e", "MEMCACHED_HOST=algo-memcached-pipeline")
    }
    elseif ($Backend -eq "neo4j") {
        $dockerRunArgs += @("-e", "NEO4J_URI=bolt://algo-neo4j-pipeline:7687")
    }
    elseif ($Backend -eq "cassandra") {
        $dockerRunArgs += @("-e", "CASSANDRA_HOSTS=algo-cassandra-pipeline")
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

    Write-Step "Call GET /reports/usage"
    $usage = Invoke-RestMethod -Uri "http://localhost:$Port/reports/usage" -Method GET
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
    
    # Cleanup database containers
    if ($Backend -eq "mongodb") {
        Write-Step "Cleaning up MongoDB container"
        docker rm -f $MongoContainer 2>$null | Out-Null
    }
    elseif ($Backend -eq "postgres") {
        Write-Step "Cleaning up PostgreSQL container"
        docker rm -f algo-postgres-pipeline 2>$null | Out-Null
    }
    elseif ($Backend -eq "memcached") {
        Write-Step "Cleaning up Memcached container"
        docker rm -f algo-memcached-pipeline 2>$null | Out-Null
    }
    elseif ($Backend -eq "neo4j") {
        Write-Step "Cleaning up Neo4j container"
        docker rm -f algo-neo4j-pipeline 2>$null | Out-Null
    }
    elseif ($Backend -eq "cassandra") {
        Write-Step "Cleaning up Cassandra container"
        docker rm -f algo-cassandra-pipeline 2>$null | Out-Null
    }
    docker network rm algo-network-pipeline 2>$null | Out-Null
}
