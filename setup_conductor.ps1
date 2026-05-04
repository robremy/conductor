[CmdletBinding()]
param(
    [string]$RepoPath = $PWD.Path,
    [string]$GroqConsoleUrl = "https://console.groq.com/keys"
)

$ErrorActionPreference = "Stop"

Write-Host "🎛️ Conductor Automated Setup" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan

# Check if GitHub CLI is available
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Host "❌ GitHub CLI (gh) is not installed. Please install it first:" -ForegroundColor Red
    Write-Host "   winget install --id GitHub.cli" -ForegroundColor Yellow
    Write-Host "   or download from: https://cli.github.com/" -ForegroundColor Yellow
    exit 1
}

# Check if authenticated with GitHub
try {
    $user = gh api user --jq '.login' 2>$null
    Write-Host "✅ Authenticated as: $user" -ForegroundColor Green
} catch {
    Write-Host "❌ Not authenticated with GitHub. Please run: gh auth login" -ForegroundColor Red
    exit 1
}

# Check if in a git repository
if (-not (Test-Path ".git")) {
    Write-Host "❌ Not in a git repository. Please run this from your project root." -ForegroundColor Red
    exit 1
}

# Get repository info
try {
    $repoInfo = gh repo view --json owner,name,isPrivate 2>$null | ConvertFrom-Json
    $repo = "$($repoInfo.owner.login)/$($repoInfo.name)"
    $isPrivate = $repoInfo.isPrivate
    Write-Host "📁 Repository: $repo ($($repoInfo.visibility))" -ForegroundColor Green
} catch {
    Write-Host "❌ Could not get repository info. Make sure you're in the correct directory." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🔑 Step 1: Groq API Key Setup" -ForegroundColor Yellow
Write-Host "Opening Groq console in your browser..." -ForegroundColor Yellow

# Open Groq console
Start-Process $GroqConsoleUrl

Write-Host ""
Write-Host "Please:" -ForegroundColor Yellow
Write-Host "1. Log in to Groq if not already logged in" -ForegroundColor Yellow
Write-Host "2. Create a new API key" -ForegroundColor Yellow
Write-Host "3. Copy the API key" -ForegroundColor Yellow
Write-Host ""

# Prompt for API key
$groqKey = Read-Host "Paste your Groq API key here" -AsSecureString
$groqKeyPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($groqKey))

if (-not $groqKeyPlain) {
    Write-Host "❌ No API key provided." -ForegroundColor Red
    exit 1
}

# Validate API key format (basic check)
if ($groqKeyPlain -notmatch '^gsk_[a-zA-Z0-9]{40,}$') {
    Write-Host "⚠️  API key format looks unusual. Please verify it's correct." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🔐 Step 2: GitHub Secrets Setup" -ForegroundColor Yellow

# Set the secret
try {
    $groqKeyPlain | gh secret set GROQ_API_KEY --repo $repo
    Write-Host "✅ GROQ_API_KEY secret set successfully" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to set GROQ_API_KEY secret: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "⚙️  Step 3: GitHub Actions Permissions" -ForegroundColor Yellow

# Check current permissions
try {
    $repoSettings = gh api repos/$repo/actions/permissions 2>$null | ConvertFrom-Json
    $currentEnabled = $repoSettings.enabled
    $currentAllowed = $repoSettings.allowed_actions

    if (-not $currentEnabled) {
        Write-Host "❌ Actions are disabled. Enabling..." -ForegroundColor Yellow
        gh api -X PUT repos/$repo/actions/permissions -f enabled=true 2>$null | Out-Null
        Write-Host "✅ Actions enabled" -ForegroundColor Green
    } else {
        Write-Host "✅ Actions already enabled" -ForegroundColor Green
    }

    # Set workflow permissions
    Write-Host "Setting workflow permissions..." -ForegroundColor Yellow
    gh api -X PUT repos/$repo/actions/permissions/workflow -f default_workflow_permissions=write -f can_approve_pull_request_reviews=true 2>$null | Out-Null
    Write-Host "✅ Workflow permissions configured" -ForegroundColor Green

} catch {
    Write-Host "⚠️  Could not verify/modify Actions permissions. You may need to do this manually in repository settings." -ForegroundColor Yellow
    Write-Host "   Go to: Settings → Actions → General → Workflow permissions: Read and write" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🏷️  Step 4: Repository Labels Setup" -ForegroundColor Yellow

# This will be handled by the workflow, but we can trigger it
Write-Host "Labels will be created automatically when the first workflow runs." -ForegroundColor Yellow

Write-Host ""
Write-Host "🎉 Setup Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Create your first issue to test Conductor" -ForegroundColor White
Write-Host "2. The auto-label workflow will prepare labels" -ForegroundColor White
Write-Host "3. When you label an issue 'agent-ready', Conductor will start working" -ForegroundColor White
Write-Host ""
Write-Host "Happy coding with Conductor! 🤖" -ForegroundColor Green