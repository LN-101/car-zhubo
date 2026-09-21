# 快速启动指南

## 一键启动所有服务

### 启动服务
```bash
cd /home/ln/AI/car-live-deployment-v3
./start_all.sh
```

这个脚本会自动：
1. ✓ 检查项目目录和 Python 环境
2. ✓ 检查端口占用情况
3. ✓ 启动 Zhubo TTS 服务（端口 8765）
4. ✓ 配置 car-live 后端使用 Zhubo TTS
5. ✓ 启动 car-live 后端服务（端口 8000）
6. ✓ 等待服务就绪并验证

### 停止服务
```bash
cd /home/ln/AI/car-live-deployment-v3
./stop_services.sh
```

或者在 `start_all.sh` 运行时按 `Ctrl+C`

## 服务地址

启动成功后，您可以访问：

| 服务 | 地址 | 说明 |
|------|------|------|
| Zhubo TTS | http://localhost:8765 | TTS 语音合成服务 |
| car-live 后端 | http://localhost:8000 | 直播管理后端 API |
| API 文档 | http://localhost:8000/docs | Swagger API 文档 |

## 测试命令

### 测试流式 TTS
```bash
curl -X POST http://localhost:8000/api/tts/stream \
  -H "Content-Type: application/json" \
  -d '{"text": "你好，这是 Zhubo TTS 测试", "voice_id": "female_warm_01"}' \
  --output test.wav
```

### 测试非流式 TTS
```bash
curl -X POST http://localhost:8000/api/tts/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "这是非流式测试", "voice_id": "female_warm_01"}' \
  --output test2.wav
```

### 检查健康状态
```bash
# 检查 Zhubo TTS
curl http://localhost:8765/health

# 检查 car-live 后端
curl http://localhost:8000/health
```

## 查看日志

### 实时查看后端日志
```bash
tail -f logs/backend.log
```

### 实时查看 Zhubo TTS 日志
```bash
tail -f logs/zhubo_tts.log
```

### 查看所有日志
```bash
ls -lh logs/
cat logs/backend.log
cat logs/zhubo_tts.log
```

## 故障排查

### 1. 端口被占用
```bash
# 查看端口占用
lsof -i :8765  # Zhubo TTS
lsof -i :8000  # car-live 后端

# 停止占用端口的进程
kill <PID>
```

### 2. 服务启动失败
```bash
# 查看详细日志
tail -50 logs/backend.log
tail -50 logs/zhubo_tts.log

# 手动启动测试
cd /home/ln/AI/zhubo
python3 main.py  # 或者 bash start.sh

cd /home/ln/AI/car-live-deployment-v3/backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 3. Zhubo TTS 连接失败
```bash
# 确认 Zhubo TTS 正在运行
curl http://localhost:8765/health

# 检查配置
cd /home/ln/AI/car-live-deployment-v3/backend
cat .env | grep ZHUBO
```

### 4. 清理所有进程
```bash
# 停止所有服务
./stop_services.sh

# 如果还有残留进程
pkill -f "uvicorn app.main:app"
pkill -f "python3 main.py"  # 根据实际 Zhubo 启动命令调整
```

## 配置说明

启动脚本会自动配置 `backend/.env` 文件：

```bash
TTS_PROVIDER=zhubo
ZHUBO_TTS_URL=http://localhost:8765
```

如需手动修改，编辑 `backend/.env` 文件即可。

## 目录结构

```
car-live-deployment-v3/
├── start_all.sh              # 一键启动脚本
├── stop_services.sh          # 停止服务脚本
├── verify_integration.sh     # 集成验证脚本
├── logs/                     # 日志目录
│   ├── backend.log          # 后端日志
│   ├── zhubo_tts.log        # Zhubo TTS 日志
│   ├── backend.pid          # 后端进程 ID
│   └── zhubo.pid            # Zhubo 进程 ID
├── backend/
│   ├── .env                 # 环境配置
│   ├── app/
│   │   ├── main.py         # 主应用（已集成 Zhubo）
│   │   ├── config.py       # 配置（已添加 zhubo_tts_url）
│   │   └── tts/
│   │       └── adapters/
│   │           └── zhubo_adapter.py  # Zhubo 适配器
│   └── test_zhubo_structure.py      # 结构测试
├── ZHUBO_TTS_INTEGRATION.md         # 详细文档
├── INTEGRATION_SUMMARY.md           # 修改总结
├── GIT_COMMIT_CHECKLIST.md          # 提交指南
└── QUICK_START.md                   # 本文档
```

## 下一步

1. 运行 `./start_all.sh` 启动所有服务
2. 访问 http://localhost:8000/docs 查看 API 文档
3. 使用上面的测试命令验证 TTS 功能
4. 开始开发或测试您的直播应用

## 更多信息

- 完整集成文档：`ZHUBO_TTS_INTEGRATION.md`
- 修改说明：`INTEGRATION_SUMMARY.md`
- Git 提交指南：`GIT_COMMIT_CHECKLIST.md`
