<#
.SYNOPSIS
    Disables Vercel deployment "success/ready" email notifications for the authenticated user.

.DESCRIPTION
    Vercel sends an email for every deployment event (production + a preview per pushed
    branch), which is the source of the constant "Successfully deployed to the following URLs"
    mail. This script turns the email channel OFF for deployment events via the Vercel REST
    API (account-level, so it also covers the wingman-githubhub project). It keeps failure
    emails on by default so you still hear about broken deploys.

    To fully stop GitHub-side "authored the thread" emails, also add the `github.silent`
    block shown in the notes below to the project's vercel.json.

.PARAMETER Token
    Vercel API token. Defaults to $env:VERCEL_TOKEN. Create one at
    https://vercel.com/account/tokens

.PARAMETER KeepErrors
    Keep emails when a deployment FAILS (default: $true).

.PARAMETER DryRun
    Fetch and show the would-be settings without writing anything.

.EXAMPLE
    $env:VERCEL_TOKEN = 'xxxx'; .\Disable-VercelDeploymentEmails.ps1
    $env:VERCEL_TOKEN = 'xxxx'; .\Disable-VercelDeploymentEmails.ps1 -DryRun
#>
[CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = 'Medium')]
param(
    [Parameter(Mandatory = $false)]
    [string] $Token = $env:VERCEL_TOKEN,

    [Parameter(Mandatory = $false)]
    [bool] $KeepErrors = $true,

    [Parameter(Mandatory = $false)]
    [switch] $DryRun
)

$ErrorActionPreference = 'Stop'

if (-not $Token) {
    Write-Error "No Vercel token provided. Set -Token or `$env:VERCEL_TOKEN (https://vercel.com/account/tokens)."
    exit 1
}

$apiBase = 'https://api.vercel.com'
$headers = @{
    Authorization = "Bearer $Token"
    'Content-Type' = 'application/json'
}

function Get-NotificationSettings {
    $resp = Invoke-RestMethod -Uri "$apiBase/v2/user/notification-settings" -Headers $headers -Method Get
    return $resp
}

function Set-NotificationSettings {
    param([Parameter(Mandatory)] $Body)
    $json = $Body | ConvertTo-Json -Depth 20 -Compress
    Write-Verbose "PATCH body: $json"
    return Invoke-RestMethod -Uri "$apiBase/v2/user/notification-settings" -Headers $headers -Method Patch -Body $json
}

try {
    $settings = Get-NotificationSettings
} catch {
    Write-Error "Failed to read current notification settings: $_"
    exit 1
}

# Ensure the email.deployment object exists.
if (-not $settings.email) { $settings | Add-Member -NotePropertyName 'email' -NotePropertyValue @{} -Force }
if (-not $settings.email.deployment) { $settings.email | Add-Member -NotePropertyName 'deployment' -NotePropertyValue @{} -Force }

$dep = $settings.email.deployment
$dep.succeeded = $false
$dep.ready     = $false
$dep.canceled  = $false
if ($KeepErrors) { $dep.error = $true } else { $dep.error = $false }

Write-Host "Proposed email.deployment settings:" -ForegroundColor Cyan
$dep | Format-Table -AutoSize | Out-String | Write-Host

if ($DryRun) {
    Write-Host "[DryRun] No changes were written." -ForegroundColor Yellow
    exit 0
}

if ($PSCmdlet.ShouldProcess("Vercel account notification settings", "disable deployment success/ready emails")) {
    try {
        $result = Set-NotificationSettings -Body $settings
        Write-Host "OK: Vercel deployment success/ready emails are now disabled for this account." -ForegroundColor Green
        Write-Host "    Failure emails: $(if ($KeepErrors) {'kept ON'} else {'disabled'})." -ForegroundColor Green
    } catch {
        Write-Error "Failed to update notification settings: $_"
        exit 1
    }
}

Write-Host ""
Write-Host "Optional next step to kill GitHub 'authored the thread' emails:" -ForegroundColor Cyan
Write-Host "  Add this to the wingman-githubhub project's vercel.json (repo root or ./redirect_server/vercel):" -ForegroundColor White
Write-Host '    { "github": { "silent": true } }' -ForegroundColor White
Write-Host "  That stops the Vercel GitHub bot from commenting on every commit/PR."
