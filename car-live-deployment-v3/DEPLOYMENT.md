# 汽车直播智能体 - 部署说明

本文档说明如何在新电脑上部署本项目，支持使用 `uv` 或传统 `pip` 环境。

## 系统要求

- **操作系统**: Windows 10/11、macOS 或 Linux
- **Python**: 3.10 或更高版本
- **Node.js**: 16.x 或更高版本（用于前端）
- **内存**: 至少 8GB RAM
- **存储**: 至少 10GB 可用空间

## 快速开始

### 1. 克隆或复制项目

```bash
# 如果从 Git 仓库克隆
git clone <repository-url>
cd test

# 或直接复制项目文件夹到目标机器
```

### 2. 使用 uv 部署（推荐）

[uv](https://github.com/astral-sh/uv) 是快速的 Python 包管理器，推荐用于新部署。

```bash
# 安装 uv（如果尚未安装）
# Windows PowerShell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# 创建虚拟环境并安装依赖
cd backend
uv venv
uv pip install -r requirements.txt

# 激活虚拟环境
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

### 3. 使用传统 pip 部署

```bash
cd backend

# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 4. 配置环境变量

复制环境变量模板并根据实际情况修改：

```bash
cd backend
cp .env.example .env
```

编辑 `.env` 文件，配置以下关键参数：

```bash
# TTS 服务配置（必须）
TTS_PROVIDER=idextts2
INDEX_TTS2_URL=http://your-tts-service:8001

# 大模型配置（可选，不配置则使用本地抽取式问答）
LLM_BASE_URL=https://api.your-llm-provider.com/v1
LLM_MODEL=your-model-name
LLM_API_KEY=your-api-key

# 数据库路径
DATABASE_URL=sqlite:///data/car_live.db

# Live2D 模型路径（可选）
# LIVE2D_MODEL_ROOT=C:\path\to\your\live2d\models
# LIVE2D_MODEL_FILE=model.model3.json
```

### 5. 安装 RAG 模型

项目使用 BGE 中文语义检索模型，首次部署需要下载：

```bash
# 在项目根目录执行
python scripts/setup_rag_models.py

# 如果无法访问 Hugging Face，使用镜像
python scripts/setup_rag_models.py --endpoint https://hf-mirror.com
```

模型文件将下载到 `models/rag/` 目录，总大小约 300MB。

### 6. 安装前端依赖

```bash
cd frontend
npm install
```

### 7. 初始化数据库

```bash
cd backend
python -c "from app.db import init_db; init_db()"
```

### 8. 启动服务

#### 方式一：使用启动脚本（Windows）

```powershell
# 在项目根目录
powershell -ExecutionPolicy Bypass -File .\start.ps1
```

#### 方式二：手动启动各服务

**启动后端 API**：
```bash
cd backend
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

**启动前端**：
```bash
cd frontend
npm run dev
# 或使用 Python 简单服务器
python -m http.server 5173
```

### 9. 访问应用

打开浏览器访问：http://127.0.0.1:5173

后端 API 文档：http://127.0.0.1:8000/docs

---

## TTS 服务部署

项目需要独立的 TTS 服务提供语音合成能力。您有以下选择：

### 选项 1：部署 IndexTTS-2.5 HTTP 服务（推荐）

**步骤**：

1. **克隆 IndexTTS-2.5 官方仓库**：
   ```bash
   git clone https://github.com/X-LANCE/IndexTTS2
   cd IndexTTS2
   ```

2. **创建虚拟环境并安装依赖**：
   ```bash
   # 使用 uv
   uv venv
   uv pip install -r requirements.txt
   
   # 或使用 pip
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

3. **下载 IndexTTS-2.5 权重**：
   ```bash
   # 根据官方文档下载模型权重到 checkpoints/ 目录
   # 确保 checkpoints/config.yaml 中 version: 2.5
   ```

4. **启动 HTTP 服务**：
   
   使用本项目提供的 HTTP 包装服务：
   ```bash
   # 复制 scripts/index_tts2_server.py 到 IndexTTS2 目录
   cp /path/to/test/scripts/index_tts2_server.py .
   
   # 启动服务
   python index_tts2_server.py --port 8001 \
     --config checkpoints/config.yaml \
     --model-dir checkpoints
   ```

5. **验证服务**：
   ```bash
   curl http://127.0.0.1:8001/health
   # 应返回: {"status": "ok", "version": "2.5"}
   ```

6. **配置本项目**：
   
   在 `backend/.env` 中设置：
   ```bash
   INDEX_TTS2_URL=http://127.0.0.1:8001
   ```

### 选项 2：使用远程 TTS 服务

如果您有远程 TTS 服务（云服务或其他服务器），直接配置 URL：

```bash
# backend/.env
INDEX_TTS2_URL=http://your-remote-tts-server:8001
```

确保远程服务实现以下 API：

- `GET /health` - 健康检查
- `POST /tts` - 语音合成
  - 请求体：`{"text": "文本", "spk_audio_prompt": "参考音频路径或 base64", "lang": "ZH", "duration_factor": 1.0}`
  - 响应：WAV 音频文件或 JSON `{"audio": "base64_audio"}`

---

## 数据准备

### 导入汽车资料

1. 准备资料文件（PDF、DOCX 或 TXT 格式）
2. 访问 http://127.0.0.1:5173
3. 进入"知识库"页面
4. 点击"批量导入"上传文件
5. 填写车型信息（品牌、车系、年款）
6. 系统自动完成向量化和索引构建

### 配置预置音色

内置音色位于 `data/preset_voices/` 目录：
- `steady-0.wav` - 沉稳阿川
- `energetic-0.wav` - 温婉小梅
- `friendly-0.wav` - 亲切阿诚

您可以替换这些文件为自己的音色样本（24kHz 单声道 WAV，3-10秒），并同步更新 catalog.json 中的 SHA-256、逐字文本与时长。

---

## 配置大模型（可选）

项目支持 OpenAI 兼容的大模型 API 增强问答能力。

### 支持的模型

- OpenAI (GPT-4, GPT-3.5)
- DeepSeek
- 智谱 AI (GLM)
- 阿里云通义千问
- 其他 OpenAI 兼容接口

### 配置方法

**方式一：通过 Web 界面**

1. 访问 http://127.0.0.1:5173
2. 进入"模型接口"页面
3. 填写 API 地址、模型名和密钥
4. 点击"保存并测试连接"

**方式二：编辑 .env 文件**

```bash
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-v4-flash
LLM_API_KEY=sk-xxxxxxxxxxxxxxxx
LLM_TIMEOUT_SECONDS=12.0
```

### 未配置大模型的行为

如果不配置大模型，系统将使用本地抽取式问答：
- 从知识库检索相关片段
- 提取关键信息作为答案
- 准确但缺乏自然语言生成能力

---

## 功能验证

### 验证 RAG 检索

访问"知识库 → 检索索引与资料检查"页面，测试查询：
- 输入问题："欧拉5纯电版多少钱？"
- 查看检索结果和相关度分数
- 确认向量检索和重排器正常工作

### 验证问答功能

在"直播台"或"数字主播"页面：
- 输入问题测试文字答案
- 检查来源溯源是否正确
- 验证大模型生成状态（如已配置）

### 验证 TTS 播报

在"直播台"页面：
- 输入一段文本
- 选择预置音色
- 点击播放
- 检查音频是否正常生成和播放

---

## 故障排查

### 问题 1：无法访问前端页面

**症状**：浏览器显示 `ERR_CONNECTION_REFUSED`

**解决方案**：
```bash
# 检查前端服务是否启动
netstat -ano | grep 5173

# 如果未启动，手动启动前端
cd frontend
python -m http.server 5173
```

### 问题 2：后端 API 无响应

**症状**：前端无法获取数据

**解决方案**：
```bash
# 检查后端服务
netstat -ano | grep 8000

# 查看后端日志
cd backend
uvicorn app.main:app --host 127.0.0.1 --port 8000 --log-level debug
```

### 问题 3：TTS 服务不可用

**症状**：播放时提示"TTS 服务未就绪"

**解决方案**：
```bash
# 检查 TTS 服务状态
curl http://127.0.0.1:8001/health

# 检查 .env 配置
cat backend/.env | grep INDEX_TTS2_URL

# 确保 INDEX_TTS2_URL 指向正确的地址
```

### 问题 4：RAG 模型缺失

**症状**：检索功能报错 "RAG models not installed"

**解决方案**：
```bash
# 重新下载模型
python scripts/setup_rag_models.py

# 检查模型文件
ls -la models/rag/
```

### 问题 5：数据库错误

**症状**：应用启动时报 "database error"

**解决方案**：
```bash
# 重新初始化数据库
rm data/car_live.db
cd backend
python -c "from app.db import init_db; init_db()"
```

---

## 性能优化建议

### 1. RAG 检索性能

- **CPU 线程数**：在 `.env` 中调整 `RAG_THREADS=4`（根据 CPU 核心数）
- **重排候选数**：调整 `RAG_RERANK_CANDIDATES=12`（更少=更快，但可能降低准确率）

### 2. TTS 延迟优化

- 使用本地 TTS 服务而非远程服务
- 启用 GPU 加速（如果 TTS 模型支持）
- 预热常用音色：首次使用会较慢，后续调用会快速

### 3. 数据库性能

对于大型知识库（>1000 个文档），考虑：
- 使用 PostgreSQL 替代 SQLite
- 调整 `MAX_DOCUMENT_BYTES` 限制大文件

---

## 生产部署建议

### 1. 使用进程管理器

**使用 systemd（Linux）**：

创建 `/etc/systemd/system/car-live-backend.service`：
```ini
[Unit]
Description=Car Live Backend API
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/test/backend
Environment="PATH=/path/to/test/backend/.venv/bin"
ExecStart=/path/to/test/backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl enable car-live-backend
sudo systemctl start car-live-backend
```

**使用 PM2（跨平台）**：
```bash
npm install -g pm2

# 启动后端
pm2 start "uvicorn app.main:app --host 0.0.0.0 --port 8000" --name car-live-backend

# 启动前端
cd frontend
pm2 start "python -m http.server 5173" --name car-live-frontend
```

### 2. 使用反向代理

**Nginx 配置示例**：
```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端
    location / {
        proxy_pass http://127.0.0.1:5173;
    }

    # 后端 API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 3. 数据备份

定期备份重要数据：
```bash
# 备份数据库
cp data/car_live.db backups/car_live_$(date +%Y%m%d).db

# 备份向量索引
tar -czf backups/rag_index_$(date +%Y%m%d).tar.gz data/*.rag-index/

# 备份上传的文件
tar -czf backups/uploads_$(date +%Y%m%d).tar.gz data/uploads/
```

---

## 开发环境设置

如果您需要继续开发项目：

### 1. 安装开发依赖

```bash
cd backend
uv pip install pytest pytest-cov black ruff mypy

# 或使用 pip
pip install pytest pytest-cov black ruff mypy
```

### 2. 运行测试

```bash
cd backend
pytest tests/ -v

# 生成覆盖率报告
pytest tests/ --cov=app --cov-report=html
```

### 3. 代码格式化

```bash
# 格式化代码
black app/ tests/

# 检查代码风格
ruff check app/ tests/

# 类型检查
mypy app/
```

### 4. 前端开发

```bash
cd frontend

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build
```

---

## 项目结构

```
test/
├── backend/              # 后端 API
│   ├── app/
│   │   ├── main.py      # FastAPI 主应用
│   │   ├── rag.py       # RAG 检索逻辑
│   │   ├── db.py        # 数据库模型
│   │   ├── tts_idextts2.py  # TTS 适配器
│   │   └── llm_gateway.py   # 大模型接口
│   ├── tests/           # 测试文件
│   ├── requirements.txt # Python 依赖
│   └── .env            # 环境变量（需创建）
├── frontend/            # 前端页面
│   ├── index.html
│   ├── app.js
│   └── style.css
├── data/               # 数据目录
│   ├── uploads/        # 用户上传文件
│   ├── preset_voices/  # 预置音色
│   └── sample/         # 示例数据
├── models/             # AI 模型
│   └── rag/           # RAG 检索模型
├── scripts/            # 工具脚本
│   ├── setup_rag_models.py      # 下载 RAG 模型
│   └── index_tts2_server.py     # TTS HTTP 服务
├── docs/               # 文档
└── README.md           # 项目说明
```

---

## 常见问题

### Q: 是否必须配置 TTS 服务？

A: 是的。项目需要 TTS 服务才能实现语音播报功能。您可以部署 IndexTTS-2.5 或使用其他兼容的 TTS 服务。

### Q: 是否必须配置大模型？

A: 不是必须的。如果不配置大模型，系统会使用本地抽取式问答，功能仍然可用，但答案会更简洁。

### Q: 如何更换为其他 TTS 引擎？

A: 实现 `/tts` API 接口即可。参考 `backend/app/tts_idextts2.py` 编写适配器，或直接使用 HTTP 模式对接远程服务。

### Q: 数据是否安全？

A: 所有数据默认存储在本地，不会自动上传到第三方服务。如果配置了大模型 API，检索到的知识片段会发送到该服务用于生成答案。

### Q: 是否支持 Docker 部署？

A: 项目暂未提供官方 Docker 镜像，但您可以根据本文档创建 Dockerfile。

---

## 技术支持

如遇问题，请检查：
1. 日志文件（如果配置了日志）
2. 浏览器控制台错误信息
3. 后端终端输出

---

## 更新日志

- **2026-09-11**: 创建部署文档，支持 uv 环境
- 简化 TTS 为纯 HTTP 接口模式
- 移除本地模型加载依赖
