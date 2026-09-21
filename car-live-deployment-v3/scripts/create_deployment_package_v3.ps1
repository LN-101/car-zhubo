# PowerShell script to create deployment package (v3)
# Final version with dropdown fix, database fix, TTS interface-only mode

$projectRoot = "C:\Users\seele\Desktop\test"
$outputPath = "C:\Users\seele\Desktop\car-live-deployment-v3.zip"
$tempDir = "C:\Users\seele\Desktop\test-deploy-temp"

Write-Host "Creating deployment package v3 (Final)..." -ForegroundColor Green
Write-Host "Includes: Dropdown fix, Database initialization, TTS interface mode" -ForegroundColor Cyan

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

# Remove user uploads (keep preset voices)
Get-ChildItem -Path "$tempDir\test\data\uploads\voices" -File | Remove-Item -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path "$tempDir\test\data\uploads\documents" -Recurse -File | Remove-Item -Force -ErrorAction SilentlyContinue

# Remove temporary files
$tempFiles = @(
    ".deployignore",
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
foreach ($file in $tempFiles) {
    Remove-Item "$tempDir\test\$file" -Force -ErrorAction SilentlyContinue
}

# Remove competition docx and old deployment scripts
Remove-Item "$tempDir\test\*.docx" -Force -ErrorAction SilentlyContinue
Remove-Item "$tempDir\test\scripts\create_deployment_package.ps1" -Force -ErrorAction SilentlyContinue
Remove-Item "$tempDir\test\scripts\create_deployment_package_v2.ps1" -Force -ErrorAction SilentlyContinue

# Create deployment checklist
$checklist = @"
# 部署检查清单

## 版本信息
- 版本: v3 (Final)
- 日期: 2026-09-11
- 主要更新:
  - ✅ 修复下拉框样式（数字主播页面音色/车型选择）
  - ✅ 修复数据库初始化问题
  - ✅ TTS 配置为纯 HTTP 接口模式
  - ✅ 更新部署文档

## 部署前准备

### 1. 系统要求
- [ ] Python 3.10+ 已安装
- [ ] Node.js 16+ 已安装
- [ ] uv 已安装（推荐）或 pip 可用
- [ ] 至少 8GB RAM
- [ ] 至少 10GB 磁盘空间

### 2. 解压文件
- [ ] 已解压 car-live-deployment-v3.zip
- [ ] 进入 test 目录

## 部署步骤

### 3. 后端环境
```bash
cd backend
uv venv
uv pip install -r requirements.txt
```

### 4. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件
```

必须配置：
- [ ] TTS_PROVIDER（gpt-sovits 或 idextts2）
- [ ] INDEX_TTS2_URL 或 GPT_SOVITS_URL

可选配置：
- [ ] LLM_BASE_URL（大模型 API）
- [ ] LLM_MODEL
- [ ] LLM_API_KEY
- [ ] LIVE2D_MODEL_ROOT（数字主播模型路径）

### 5. ⭐ 初始化数据库（关键步骤）
```bash
python -c "from app.db import init_db; init_db()"
```

验证数据库：
- [ ] data/car_live.db 文件存在
- [ ] 文件大小 > 60KB

### 6. 下载 RAG 模型
```bash
python scripts/setup_rag_models.py
```

### 7. 前端依赖
```bash
cd ../frontend
npm install
```

### 8. 启动服务
```bash
cd ..
powershell -ExecutionPolicy Bypass -File .\start.ps1
```

## 部署 TTS 服务（必须）

### 选项 A: IndexTTS-2.5
1. [ ] 克隆 IndexTTS2 仓库
2. [ ] 下载模型权重到 checkpoints/
3. [ ] 启动 HTTP 服务：
```bash
python scripts/index_tts2_server.py --port 8001 \
  --config checkpoints/config.yaml \
  --model-dir checkpoints
```
4. [ ] 配置 .env: INDEX_TTS2_URL=http://127.0.0.1:8001

### 选项 B: GPT-SoVITS
1. [ ] 启动 GPT-SoVITS 服务（端口 9880）
2. [ ] 配置 .env: GPT_SOVITS_URL=http://127.0.0.1:9880

## 验证部署

### 9. 检查服务状态
- [ ] 前端: http://127.0.0.1:5173 可访问
- [ ] 后端: http://127.0.0.1:8000/docs 可访问
- [ ] TTS 服务可连接

### 10. 功能测试
- [ ] 知识库：可以导入文档
- [ ] 检索：可以搜索并返回结果
- [ ] 问答：可以生成答案（需配置 LLM）
- [ ] 语音播报：可以生成语音
- [ ] 数字主播：下拉框样式正常，可以播报

### 11. UI 验证
- [ ] 数字主播页面下拉框显示深色背景
- [ ] 音色和车型选择框可以正常使用
- [ ] 悬停时有蓝色高亮效果

## 常见问题

### Q1: 启动后提示 "Internal Server Error"
A: 检查数据库是否已初始化
```bash
ls -lh data/car_live.db  # 应该 > 60KB
```
如果是 0 字节，重新初始化：
```bash
python -c "from app.db import init_db; init_db()"
```

### Q2: TTS 服务不可用
A: 检查 TTS 服务状态
```bash
curl http://127.0.0.1:8001/health  # IndexTTS
curl http://127.0.0.1:9880/        # GPT-SoVITS
```

### Q3: 下拉框显示白色
A: 强制刷新浏览器缓存
- Ctrl + F5 强制刷新
- 或使用无痕模式测试

### Q4: RAG 模型下载失败
A: 使用镜像下载
```bash
python scripts/setup_rag_models.py --endpoint https://hf-mirror.com
```

## 部署完成

所有步骤完成后，系统应该可以正常运行。

访问: http://127.0.0.1:5173

如有问题，参考 DEPLOYMENT.md 详细文档。
"@

Set-Content -Path "$tempDir\test\部署检查清单.txt" -Value $checklist -Encoding UTF8

# Create release notes
$releaseNotes = @"
# 汽车直播智能体 - 部署包 v3 发布说明

## 版本信息
- **版本号**: v3 (Final Release)
- **发布日期**: 2026-09-11
- **包大小**: 约 1.3 GB

## 🎉 主要更新

### 1. UI 修复
- ✅ **修复下拉框样式问题**
  - 数字主播页面的音色和车型下拉框现在显示为深色主题
  - 选项背景：深黑色（#0a0e14）
  - 悬停效果：科技蓝渐变高亮
  - 选中状态：科技蓝到电光蓝渐变
  - 自定义滚动条：科技蓝渐变

### 2. 数据库修复
- ✅ **解决空数据库问题**
  - 部署包不再包含数据库文件
  - 目标机器首次启动前必须初始化数据库
  - 防止 "Internal Server Error" 问题

### 3. TTS 配置优化
- ✅ **纯 HTTP 接口模式**
  - 移除本地模型加载配置
  - 支持 IndexTTS-2.5 和 GPT-SoVITS
  - 清晰的配置文档和示例

### 4. 部署体验改进
- ✅ 新增"部署检查清单.txt"
- ✅ 更新 DEPLOYMENT.md 文档
- ✅ 优化 .env.example 配置模板

## 📦 包含内容

### 核心代码
- ✅ 完整的后端 API（FastAPI）
- ✅ 完整的前端界面（已修复下拉框样式）
- ✅ RAG 检索系统
- ✅ 大模型接口适配器
- ✅ TTS 接口适配器
- ✅ Live2D 数字主播
- ✅ 音色克隆功能

### 数据资源
- ✅ 预置音色样本（3 个）
- ✅ 示例数据文件
- ✅ Live2D 模型加载器

### 工具脚本
- ✅ RAG 模型下载脚本
- ✅ IndexTTS HTTP 服务脚本
- ✅ 数据库初始化脚本
- ✅ 服务启动脚本

### 文档
- ✅ DEPLOYMENT.md（完整部署指南）
- ✅ 部署检查清单.txt（逐步指南）
- ✅ README.md（项目说明）
- ✅ docs/ 目录下的详细文档

## 🚀 快速开始

```bash
# 1. 解压
unzip car-live-deployment-v3.zip

# 2. 创建环境
cd test/backend
uv venv
uv pip install -r requirements.txt

# 3. 配置
cp .env.example .env
# 编辑 .env 文件

# 4. 初始化数据库（重要！）
python -c "from app.db import init_db; init_db()"

# 5. 下载 RAG 模型
python scripts/setup_rag_models.py

# 6. 启动服务
cd ..
powershell -ExecutionPolicy Bypass -File .\start.ps1
```

## ⚠️ 重要提示

### 必须配置 TTS 服务
项目需要独立的 TTS 服务才能使用语音播报功能：
- **IndexTTS-2.5**: 更快，支持语速控制
- **GPT-SoVITS**: 更自然，情感表现力强

详见 DEPLOYMENT.md 第 7 章。

### 数据库初始化
首次部署必须手动初始化数据库，否则会出现 "Internal Server Error"：
```bash
python -c "from app.db import init_db; init_db()"
```

### RAG 模型下载
首次使用检索功能前需要下载约 300MB 的语义模型：
```bash
python scripts/setup_rag_models.py
```

## 📋 系统要求

- Python 3.10+
- Node.js 16+
- 8GB+ RAM
- 10GB+ 磁盘空间
- Windows 10/11, macOS, 或 Linux

## 🎯 功能特性

### 核心功能
- ✅ 企业级 RAG 知识库（BGE 语义检索）
- ✅ 大模型问答生成（OpenAI 兼容 API）
- ✅ 流式 TTS 动态播报（HTTP 接口）
- ✅ Live2D 数字主播（嘴型同步）
- ✅ 音色克隆（上传样本 + 麦克风录制）

### 扩展功能
- ✅ 直播统计分析
- ✅ 数据合规方案
- ✅ 话术生成接口
- ✅ 效果验证工具
- ✅ 音色听测评分

## 🆚 版本对比

| 项目 | v1 | v2 | v3 (当前) |
|------|----|----|-----------|
| 下拉框样式 | ❌ 白色 | ❌ 白色 | ✅ 深色科技风 |
| 数据库问题 | ❌ 空文件 | ✅ 移除 | ✅ 移除 + 说明 |
| 部署说明 | ⚠️ 基础 | ✅ 详细 | ✅ 完整 + 清单 |
| TTS 配置 | ⚠️ 混合 | ✅ HTTP | ✅ HTTP + 文档 |
| 包大小 | 1.38 GB | 1.38 GB | ~1.3 GB |

## 📞 技术支持

如遇问题：
1. 查看"部署检查清单.txt"
2. 参考 DEPLOYMENT.md 故障排查章节
3. 检查浏览器控制台和后端日志

## 🎉 感谢使用

汽车直播智能体 v3 是一个完整的、可投入生产的智能对话系统。

祝您部署顺利！
"@

Set-Content -Path "$tempDir\test\发布说明.txt" -Value $releaseNotes -Encoding UTF8

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
Write-Host "Deployment package v3 (Final) created!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host "Location: $outputPath" -ForegroundColor Cyan

# Show package size
$size = (Get-Item $outputPath).Length / 1MB
Write-Host "Package size: $([math]::Round($size, 2)) MB" -ForegroundColor Cyan
Write-Host ""
Write-Host "What's new in v3:" -ForegroundColor Yellow
Write-Host "  ✅ Fixed dropdown styles (dark theme)" -ForegroundColor White
Write-Host "  ✅ Fixed database initialization issue" -ForegroundColor White
Write-Host "  ✅ TTS interface-only mode (HTTP)" -ForegroundColor White
Write-Host "  ✅ Added deployment checklist" -ForegroundColor White
Write-Host "  ✅ Added release notes" -ForegroundColor White
Write-Host ""
Write-Host "Ready for deployment!" -ForegroundColor Green
