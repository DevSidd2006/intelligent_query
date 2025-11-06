#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Push Docker image to Docker Hub
.DESCRIPTION
    Tags and pushes the intelligent-query Docker image to Docker Hub
.PARAMETER DockerHubUsername
    Your Docker Hub username
.PARAMETER ImageVersion
    Version tag for the image (default: latest and v1.0.0)
.EXAMPLE
    ./push_to_docker_hub.ps1 -DockerHubUsername "your-username"
#>

param(
    [Parameter(Mandatory = $true, HelpMessage = "Your Docker Hub username")]
    [string]$DockerHubUsername,
    
    [Parameter(Mandatory = $false, HelpMessage = "Image version (default: latest, v1.0.0)")]
    [string[]]$ImageVersion = @("latest", "v1.0.0")
)

$ErrorActionPreference = "Stop"

Write-Host "╔════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   Docker Hub Push Script               ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Check Docker is running
Write-Host "🔍 Checking Docker daemon..." -ForegroundColor Yellow
try {
    docker ps > $null 2>&1
    Write-Host "✓ Docker is running" -ForegroundColor Green
}
catch {
    Write-Host "✗ Docker is not running. Please start Docker Desktop." -ForegroundColor Red
    exit 1
}

# Check authentication
Write-Host "🔐 Checking Docker authentication..." -ForegroundColor Yellow
try {
    $authTest = docker ps 2>&1
    if ($authTest -match "permission denied") {
        Write-Host "✗ Not authenticated to Docker Hub" -ForegroundColor Red
        Write-Host "  Run: docker login" -ForegroundColor Yellow
        exit 1
    }
    Write-Host "✓ Docker authentication verified" -ForegroundColor Green
}
catch {
    Write-Host "✗ Authentication check failed" -ForegroundColor Red
    exit 1
}

# Get current image
Write-Host "`n📦 Fetching Docker image information..." -ForegroundColor Yellow
$imageInfo = docker images | Select-String "intelligent_query-pdf-qa-app"

if (-not $imageInfo) {
    Write-Host "✗ Docker image not found" -ForegroundColor Red
    Write-Host "  Available images:" -ForegroundColor Yellow
    docker images
    exit 1
}

$imageName = "intelligent_query-pdf-qa-app"
Write-Host "✓ Found image: $imageName" -ForegroundColor Green
Write-Host $imageInfo

# Tag images
Write-Host "`n🏷️  Tagging images for Docker Hub..." -ForegroundColor Yellow

foreach ($tag in $ImageVersion) {
    $sourceTag = "$imageName`:latest"
    $targetTag = "$DockerHubUsername/intelligent-query:$tag"
    
    Write-Host "  → Tagging: $sourceTag → $targetTag"
    docker tag $sourceTag $targetTag
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ Failed to tag image: $targetTag" -ForegroundColor Red
        exit 1
    }
    Write-Host "    ✓ Tagged successfully" -ForegroundColor Green
}

# Show tagged images
Write-Host "`n📋 Tagged images:" -ForegroundColor Yellow
docker images | Select-String "$DockerHubUsername/intelligent-query"

# Push images
Write-Host "`n📤 Pushing images to Docker Hub..." -ForegroundColor Yellow
Write-Host "  Repository: https://hub.docker.com/r/$DockerHubUsername/intelligent-query" -ForegroundColor Cyan
Write-Host ""

foreach ($tag in $ImageVersion) {
    $pushTag = "$DockerHubUsername/intelligent-query:$tag"
    
    Write-Host "  → Pushing: $pushTag" -ForegroundColor Cyan
    $startTime = Get-Date
    
    docker push $pushTag
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "    ✗ Push failed" -ForegroundColor Red
        Write-Host "`n    Troubleshooting:" -ForegroundColor Yellow
        Write-Host "    1. Make sure the repository exists on Docker Hub" -ForegroundColor Yellow
        Write-Host "    2. Visit: https://hub.docker.com/repository/create" -ForegroundColor Yellow
        Write-Host "    3. Create repository named: intelligent-query" -ForegroundColor Yellow
        Write-Host "    4. Then run this script again" -ForegroundColor Yellow
        exit 1
    }
    
    $endTime = Get-Date
    $duration = ($endTime - $startTime).TotalSeconds
    Write-Host "    ✓ Push completed in $([math]::Round($duration, 2))s" -ForegroundColor Green
}

# Success message
Write-Host "`n╔════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║   ✓ Success! Image pushed to Hub      ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════╝" -ForegroundColor Green

Write-Host "`n📚 Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Visit your repository:" -ForegroundColor Yellow
Write-Host "     https://hub.docker.com/r/$DockerHubUsername/intelligent-query" -ForegroundColor Cyan
Write-Host "`n  2. Pull the image:" -ForegroundColor Yellow
Write-Host "     docker pull $DockerHubUsername/intelligent-query:latest" -ForegroundColor Cyan
Write-Host "`n  3. Run the container:" -ForegroundColor Yellow
Write-Host "     docker run -p 5000:5000 --env-file .env $DockerHubUsername/intelligent-query:latest" -ForegroundColor Cyan
Write-Host ""
