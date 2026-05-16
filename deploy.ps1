param(
    [string]$CommitMessage = "",
    [switch]$SkipGit,
    [switch]$ApiOnly,
    [switch]$WebOnly
)

$ErrorActionPreference = "Stop"

# =========================================================
# MedNexa AI - Azure Deploy Script
# Run from: C:\projects\MedNexaAI
# =========================================================

# ---------- Azure Settings ----------
$RG = "rg-mednexa-ai-dev"
$LOC = "centralus"

$ACR_NAME = "acrmednexaidev"
$ACR_LOGIN_SERVER = "$ACR_NAME.azurecr.io"

$ENV_NAME = "cae-mednexa-ai-dev"

$API_APP_NAME = "mednexa-api-dev"
$WEB_APP_NAME = "mednexa-web-dev"

$API_IMAGE_NAME = "mednexa-api"
$WEB_IMAGE_NAME = "mednexa-web"

# ---------- PostgreSQL ----------
$PG_HOST = "pg-mednexa-ai-dev.postgres.database.azure.com"
$PG_DB = "mednexa"
$PG_USER = "mednexa_admin"

# IMPORTANT:
# Set this as local environment variable before running:
# $env:MEDNEXA_DB_PASSWORD="your-postgres-password"
if ([string]::IsNullOrWhiteSpace($env:MEDNEXA_DB_PASSWORD)) {
    Write-Host "ERROR: MEDNEXA_DB_PASSWORD environment variable is missing." -ForegroundColor Red
    Write-Host "Run this first in PowerShell:" -ForegroundColor Yellow
    Write-Host '$env:MEDNEXA_DB_PASSWORD="your-postgres-password"' -ForegroundColor Yellow
    exit 1
}

$DATABASE_URL = "postgresql+psycopg2://${PG_USER}:$($env:MEDNEXA_DB_PASSWORD)@${PG_HOST}:5432/${PG_DB}?sslmode=require"

# ---------- Validate location ----------
$PROJECT_ROOT = Get-Location
if (!(Test-Path "$PROJECT_ROOT\apps\api") -or !(Test-Path "$PROJECT_ROOT\apps\web")) {
    Write-Host "ERROR: Run deploy.ps1 from project root C:\projects\MedNexaAI" -ForegroundColor Red
    exit 1
}

# ---------- Tag ----------
$timestamp = Get-Date -Format "yyyyMMddHHmmss"
$gitSha = "local"
try {
    $gitSha = git rev-parse --short HEAD
} catch {
    $gitSha = "local"
}
$TAG = "$timestamp-$gitSha"

$API_IMAGE = "$ACR_LOGIN_SERVER/${API_IMAGE_NAME}:$TAG"
$WEB_IMAGE = "$ACR_LOGIN_SERVER/${WEB_IMAGE_NAME}:$TAG"

Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "MedNexa AI Deploy" -ForegroundColor Cyan
Write-Host "Resource Group : $RG"
Write-Host "ACR            : $ACR_NAME"
Write-Host "Tag            : $TAG"
Write-Host "API Image      : $API_IMAGE"
Write-Host "WEB Image      : $WEB_IMAGE"
Write-Host "=================================================" -ForegroundColor Cyan

# ---------- Azure login check ----------
Write-Host "`nChecking Azure login..." -ForegroundColor Cyan
az account show 1>$null

# ---------- Ensure Container Apps extension ----------
Write-Host "Ensuring Azure Container Apps extension..." -ForegroundColor Cyan
az extension add --name containerapp --upgrade --allow-preview true

# ---------- Ensure Container Apps Environment ----------
Write-Host "`nChecking Container Apps environment..." -ForegroundColor Cyan
$envExists = $true
try {
    az containerapp env show --name $ENV_NAME --resource-group $RG 1>$null
} catch {
    $envExists = $false
}

if (-not $envExists) {
    Write-Host "Creating Container Apps environment: $ENV_NAME" -ForegroundColor Yellow
    az containerapp env create `
        --name $ENV_NAME `
        --resource-group $RG `
        --location $LOC
} else {
    Write-Host "Container Apps environment exists: $ENV_NAME" -ForegroundColor Green
}

# ---------- Get ACR Credentials ----------
Write-Host "`nGetting ACR credentials..." -ForegroundColor Cyan
$ACR_USER = az acr credential show --name $ACR_NAME --query "username" -o tsv
$ACR_PASS = az acr credential show --name $ACR_NAME --query "passwords[0].value" -o tsv

# ---------- Build API Image ----------
if (-not $WebOnly) {
    Write-Host "`nBuilding API image in ACR..." -ForegroundColor Cyan

    az acr build `
        --registry $ACR_NAME `
        --image "${API_IMAGE_NAME}:$TAG" `
        --file "apps/api/Dockerfile" `
        "apps/api"
}

# ---------- Deploy API ----------
if (-not $WebOnly) {
    Write-Host "`nChecking API Container App..." -ForegroundColor Cyan

    $apiExists = $true
    try {
        az containerapp show --name $API_APP_NAME --resource-group $RG 1>$null
    } catch {
        $apiExists = $false
    }

    if (-not $apiExists) {
        Write-Host "Creating API Container App..." -ForegroundColor Yellow

        az containerapp create `
            --name $API_APP_NAME `
            --resource-group $RG `
            --environment $ENV_NAME `
            --image $API_IMAGE `
            --target-port 8000 `
            --ingress external `
            --registry-server $ACR_LOGIN_SERVER `
            --registry-username $ACR_USER `
            --registry-password $ACR_PASS `
            --secrets "database-url=$DATABASE_URL" `
            --env-vars "DATABASE_URL=secretref:database-url" "APP_ENV=dev" `
            --cpu 0.5 `
            --memory 1.0Gi `
            --min-replicas 1 `
            --max-replicas 3
    } else {
        Write-Host "Updating API Container App..." -ForegroundColor Yellow

        az containerapp secret set `
            --name $API_APP_NAME `
            --resource-group $RG `
            --secrets "database-url=$DATABASE_URL"

        az containerapp update `
            --name $API_APP_NAME `
            --resource-group $RG `
            --image $API_IMAGE `
            --set-env-vars "DATABASE_URL=secretref:database-url" "APP_ENV=dev"
    }
}

# ---------- Get API URL ----------
Write-Host "`nGetting API URL..." -ForegroundColor Cyan
$API_FQDN = az containerapp show `
    --name $API_APP_NAME `
    --resource-group $RG `
    --query "properties.configuration.ingress.fqdn" `
    -o tsv

$API_URL = "https://$API_FQDN"

Write-Host "API URL: $API_URL" -ForegroundColor Green

# ---------- Build Web Image ----------
if (-not $ApiOnly) {
    Write-Host "`nBuilding Web image in ACR..." -ForegroundColor Cyan

    az acr build `
        --registry $ACR_NAME `
        --image "${WEB_IMAGE_NAME}:$TAG" `
        --file "apps/web/Dockerfile" `
        --build-arg "NEXT_PUBLIC_API_BASE_URL=$API_URL" `
        "apps/web"
}

# ---------- Deploy Web ----------
if (-not $ApiOnly) {
    Write-Host "`nChecking Web Container App..." -ForegroundColor Cyan

    $webExists = $true
    try {
        az containerapp show --name $WEB_APP_NAME --resource-group $RG 1>$null
    } catch {
        $webExists = $false
    }

    if (-not $webExists) {
        Write-Host "Creating Web Container App..." -ForegroundColor Yellow

        az containerapp create `
            --name $WEB_APP_NAME `
            --resource-group $RG `
            --environment $ENV_NAME `
            --image $WEB_IMAGE `
            --target-port 3000 `
            --ingress external `
            --registry-server $ACR_LOGIN_SERVER `
            --registry-username $ACR_USER `
            --registry-password $ACR_PASS `
            --env-vars "NEXT_PUBLIC_API_BASE_URL=$API_URL" `
            --cpu 0.5 `
            --memory 1.0Gi `
            --min-replicas 1 `
            --max-replicas 3
    } else {
        Write-Host "Updating Web Container App..." -ForegroundColor Yellow

        az containerapp update `
            --name $WEB_APP_NAME `
            --resource-group $RG `
            --image $WEB_IMAGE `
            --set-env-vars "NEXT_PUBLIC_API_BASE_URL=$API_URL"
    }
}

# ---------- Get Web URL ----------
$WEB_URL = ""
if (-not $ApiOnly) {
    Write-Host "`nGetting Web URL..." -ForegroundColor Cyan

    $WEB_FQDN = az containerapp show `
        --name $WEB_APP_NAME `
        --resource-group $RG `
        --query "properties.configuration.ingress.fqdn" `
        -o tsv

    $WEB_URL = "https://$WEB_FQDN"

    Write-Host "WEB URL: $WEB_URL" -ForegroundColor Green
}

# ---------- Optional Git Push ----------
if (-not $SkipGit) {
    Write-Host "`nGit status..." -ForegroundColor Cyan
    git status

    if ([string]::IsNullOrWhiteSpace($CommitMessage)) {
        Write-Host "`nNo commit message passed. Skipping git commit/push." -ForegroundColor Yellow
        Write-Host "To push with deploy, use:" -ForegroundColor Yellow
        Write-Host '.\deploy.ps1 -CommitMessage "your message"' -ForegroundColor Yellow
    } else {
        Write-Host "`nCommitting and pushing to GitHub..." -ForegroundColor Cyan
        git add .
        git commit -m $CommitMessage
        git push origin main
    }
}

# ---------- Health Checks ----------
Write-Host "`nTesting API health..." -ForegroundColor Cyan
try {
    $health = Invoke-RestMethod -Uri "$API_URL/health" -Method GET
    Write-Host "API health OK:" -ForegroundColor Green
    $health | ConvertTo-Json
} catch {
    Write-Host "API health check failed. Check logs:" -ForegroundColor Yellow
    Write-Host "az containerapp logs show --name $API_APP_NAME --resource-group $RG --follow"
}

Write-Host "`n=================================================" -ForegroundColor Cyan
Write-Host "DEPLOY COMPLETE" -ForegroundColor Green
Write-Host "API: $API_URL"
if (-not $ApiOnly) {
    Write-Host "WEB: $WEB_URL"
}
Write-Host "=================================================" -ForegroundColor Cyan
