# PowerShell script to create deployment package (v2)
# Fixes: Remove empty database file and ensure clean deployment

$projectRoot = "C:\Users\seele\Desktop\test"
$outputPath = "C:\Users\seele\Desktop\car-live-deployment-v2.zip"
$tempDir = "C:\Users\seele\Desktop\test-deploy-temp"

Write-Host "Creating deployment package v2..." -ForegroundColor Green
Write-Host "Improvements: Database will be created fresh on target machine" -ForegroundColor Cyan

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
Remove-Item "$tempDir\test\backend\.pytest_cache" -Recurse -Force -ErrorAction SilentlyContinue

# Remove node_modules
Remove-Item "$tempDir\test\node_modules" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "$tempDir\test\frontend\node_modules" -Recurse -Force -ErrorAction SilentlyContinue

# Remove .git
Remove-Item "$tempDir\test\.git" -Recurse -Force -ErrorAction SilentlyContinue

# IMPORTANT: Remove database file completely (will be created fresh on target)
Remove-Item "$tempDir\test\data\car_live.db" -Force -ErrorAction SilentlyContinue
Write-Host "  - Removed database file (will be initialized on target machine)" -ForegroundColor Yellow

# Remove RAG indexes
Get-ChildItem -Path "$tempDir\test\data" -Recurse -Directory -Filter "*.rag-index" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

# Remove models (will be downloaded on target)
Remove-Item "$tempDir\test\models\rag" -Recurse -Force -ErrorAction SilentlyContinue

# Remove test artifacts
Remove-Item "$tempDir\test\artifacts\acceptance-*" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "$tempDir\test\artifacts\implementation-*" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "$tempDir\test\artifacts\rag-upgrade-*" -Recurse -Force -ErrorAction SilentlyContinue

# Remove .env (keep .env.example)
Remove-Item "$tempDir\test\backend\.env" -Force -ErrorAction SilentlyContinue

# Remove user uploads
Get-ChildItem -Path "$tempDir\test\data\uploads" -Recurse -File | Remove-Item -Force -ErrorAction SilentlyContinue

# Remove temporary markdown files
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
    "INDEXTTS_25_SWITCH_COMPLETED.md",
    "COMPETITION_COMPLIANCE_REPORT.md"
)
foreach ($file in $tempMdFiles) {
    Remove-Item "$tempDir\test\$file" -Force -ErrorAction SilentlyContinue
}

# Remove competition docx
Remove-Item "$tempDir\test\*.docx" -Force -ErrorAction SilentlyContinue

# Remove .deployignore
Remove-Item "$tempDir\test\.deployignore" -Force -ErrorAction SilentlyContinue

# Create deployment instruction file
$deployInstruction = @"
# 部署前必读

## 首次部署步骤

1. 解压此压缩包到目标目录
2. 进入项目目录: cd test/backend
3. 创建虚拟环境（推荐使用 uv）:
   - uv venv
   - uv pip install -r requirements.txt
4. 配置环境变量:
   - cp .env.example .env
   - 编辑 .env 文件，配置 TTS URL 和 LLM API
5. **重要**: 初始化数据库
   - python -c "from app.db import init_db; init_db()"
6. 下载 RAG 模型:
   - python scripts/setup_rag_models.py
7. 安装前端依赖:
   - cd ../frontend
   - npm install
8. 启动服务:
   - cd ..
   - powershell -ExecutionPolicy Bypass -File .\start.ps1

详细步骤请参考 DEPLOYMENT.md 文档。

## 注意事项

- 数据库文件已从部署包中移除，首次启动前必须运行初始化命令
- RAG 模型需要在目标机器上下载（约300MB）
- TTS 服务需要独立部署
- 虚拟环境需要在目标机器上重新创建

## 常见问题

Q: 启动后显示"Internal Server Error"？
A: 检查是否已初始化数据库，运行: python -c "from app.db import init_db; init_db()"

Q: 如何验证数据库已正确初始化？
A: 检查 data/car_live.db 文件大小应该大于 60KB

完整文档: DEPLOYMENT.md
"@

Set-Content -Path "$tempDir\test\部署说明.txt" -Value $deployInstruction -Encoding UTF8

# Create zip archive
Write-Host "Creating zip archive..."
if (Test-Path $outputPath) {
    Remove-Item $outputPath -Force
}

Add-Type -Assembly System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory("$tempDir\test", $outputPath, [System.IO.Compression.CompressionLevel]::Optimal, $false)

# Clean up temp directory
Remove-Item $tempDir -Recurse -Force

Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "Deployment package v2 created successfully!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host "Location: $outputPath" -ForegroundColor Cyan

# Show package size
$size = (Get-Item $outputPath).Length / 1MB
Write-Host "Package size: $([math]::Round($size, 2)) MB" -ForegroundColor Cyan
Write-Host ""
Write-Host "Improvements in v2:" -ForegroundColor Yellow
Write-Host "  - Database file removed (prevents empty DB issue)" -ForegroundColor White
Write-Host "  - Added deployment instruction file (部署说明.txt)" -ForegroundColor White
Write-Host "  - Cleaned up all temporary files" -ForegroundColor White
Write-Host ""
Write-Host "Target machine must:" -ForegroundColor Yellow
Write-Host "  1. Create virtual environment" -ForegroundColor White
Write-Host "  2. Initialize database (critical!)" -ForegroundColor White
Write-Host "  3. Download RAG models" -ForegroundColor White
Write-Host "  4. Configure .env file" -ForegroundColor White
