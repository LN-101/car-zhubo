# PowerShell script to create deployment package
# Excludes development files, caches, and runtime data

$projectRoot = "C:\Users\seele\Desktop\test"
$outputPath = "C:\Users\seele\Desktop\car-live-deployment.zip"
$tempDir = "C:\Users\seele\Desktop\test-deploy-temp"

Write-Host "Creating deployment package..." -ForegroundColor Green

# Create temporary directory
if (Test-Path $tempDir) {
    Remove-Item $tempDir -Recurse -Force
}
New-Item -ItemType Directory -Path $tempDir | Out-Null

# Copy project files
Write-Host "Copying project files..."
Copy-Item -Path $projectRoot -Destination $tempDir -Recurse -Force

# Remove excluded items
Write-Host "Cleaning up unnecessary files..."

# Remove virtual environments
Remove-Item "$tempDir\test\.venv" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "$tempDir\test\venv" -Recurse -Force -ErrorAction SilentlyContinue

# Remove Python cache
Get-ChildItem -Path "$tempDir\test" -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path "$tempDir\test" -Recurse -File -Filter "*.pyc" | Remove-Item -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path "$tempDir\test" -Recurse -File -Filter "*.pyo" | Remove-Item -Force -ErrorAction SilentlyContinue
Remove-Item "$tempDir\test\.pytest_cache" -Recurse -Force -ErrorAction SilentlyContinue

# Remove node_modules
Remove-Item "$tempDir\test\node_modules" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "$tempDir\test\frontend\node_modules" -Recurse -Force -ErrorAction SilentlyContinue

# Remove .git
Remove-Item "$tempDir\test\.git" -Recurse -Force -ErrorAction SilentlyContinue

# Remove runtime data
Remove-Item "$tempDir\test\data\car_live.db" -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path "$tempDir\test\data" -Recurse -Directory -Filter "*.rag-index" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

# Remove models (will be downloaded on target)
Remove-Item "$tempDir\test\models\rag" -Recurse -Force -ErrorAction SilentlyContinue

# Remove test artifacts
Remove-Item "$tempDir\test\artifacts\acceptance-*" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "$tempDir\test\artifacts\implementation-*" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "$tempDir\test\artifacts\rag-upgrade-*" -Recurse -Force -ErrorAction SilentlyContinue

# Remove .env (keep .env.example)
Remove-Item "$tempDir\test\backend\.env" -Force -ErrorAction SilentlyContinue

# Remove temporary markdown files (already cleaned)
$tempMdFiles = @(
    "ACCEPTANCE_CHECKLIST.md",
    "CONNECTION_FIX.md",
    "DIALOG_STYLE_FIX.md",
    "FINAL_ANALYSIS.md",
    "FINAL_OPTIMIZATION_SUMMARY.md",
    "FINAL_SOLUTION.md",
    "OPTIMIZATION_COMPLETE.md",
    "OPTIMIZATION_REPORT.md",
    "OPTIMIZATION_SUMMARY.md",
    "PERFORMANCE_OPTIMIZATION.md",
    "PERFORMANCE_TEST_RESULTS.md",
    "QUICK_FIX_GUIDE.md",
    "ROOT_CAUSE_FOUND.md",
    "SCRIPT_INPUT_OPTIMIZATION.md",
    "SERVICE_OFFLINE_FIX.md",
    "SUMMARY.md",
    "SWITCH_VERIFICATION.md",
    "TTS_PERFORMANCE_DIAGNOSIS.md",
    "TTS_URGENT_FIX.md",
    "INDEXTTS_25_SWITCH_COMPLETED.md"
)
foreach ($file in $tempMdFiles) {
    Remove-Item "$tempDir\test\$file" -Force -ErrorAction SilentlyContinue
}

# Remove competition submission docx (user's source file)
Remove-Item "$tempDir\test\6.*docx" -Force -ErrorAction SilentlyContinue

# Create zip archive
Write-Host "Creating zip archive..."
if (Test-Path $outputPath) {
    Remove-Item $outputPath -Force
}

# Use .NET compression for better compatibility
Add-Type -Assembly System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory("$tempDir\test", $outputPath, [System.IO.Compression.CompressionLevel]::Optimal, $false)

# Clean up temp directory
Remove-Item $tempDir -Recurse -Force

Write-Host "Deployment package created successfully!" -ForegroundColor Green
Write-Host "Location: $outputPath" -ForegroundColor Cyan

# Show package size
$size = (Get-Item $outputPath).Length / 1MB
Write-Host "Package size: $([math]::Round($size, 2)) MB" -ForegroundColor Cyan
