# Zhubo TTS 集成说明

本文档说明如何在 car-live-deployment-v3 中使用 Zhubo TTS 服务。

## 集成内容

### 1. 新增文件
- `backend/app/tts/adapters/zhubo_adapter.py` - Zhubo TTS 适配器

### 2. 修改文件
- `backend/app/config.py` - 添加 `zhubo_tts_url` 配置项
- `backend/app/main.py` - 集成 Zhubo TTS 提供者支持
- `backend/.env.example` - 添加 Zhubo 配置示例

## 配置方法

### 1. 环境变量配置

在 `backend/.env` 文件中添加或修改以下配置：

```bash
# 设置 TTS 提供者为 zhubo
TTS_PROVIDER=zhubo

# 配置 Zhubo TTS 服务地址
ZHUBO_TTS_URL=http://localhost:8765
```

### 2. Zhubo TTS 服务要求

Zhubo TTS 服务需要提供以下 API 端点：

#### 健康检查端点
```
GET /health
返回: 200 OK
```

#### 语音合成端点
```
POST /tts/synthesize
Content-Type: application/json

请求体:
{
  "text": "要合成的文本",
  "speaker": "female1",           // 说话人 ID
  "speed": 1.0,                   // 语速倍率
  "tone": "neutral",              // 语调/情感
  "intensity": 0.3,               // 强度
  "volume": 1.0                   // 音量
}

返回: WAV 格式音频数据（二进制）
```

## 语音 ID 映射

car-live 的 voice_id 会自动映射到 Zhubo 的 speaker 格式：

| car-live voice_id | Zhubo speaker |
|-------------------|---------------|
| female_warm_01 | female1 |
| female_energetic_01 | female2 |
| male_steady_01 | male1 |
| female_professional | female1 |
| male_confident | male1 |

其他格式的 voice_id 会尝试自动解析，例如：
- `female_xxx_01` → `female1`
- `male_xxx_02` → `male2`

## 使用方法

### 启动服务

1. 确保 Zhubo TTS 服务已启动并运行在配置的地址上
2. 启动 car-live-deployment-v3 后端：

```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### API 调用示例

#### 流式 TTS
```bash
curl -X POST http://localhost:8000/api/tts/stream \
  -H "Content-Type: application/json" \
  -d '{
    "text": "你好，这是 Zhubo TTS 测试",
    "voice_id": "female_warm_01",
    "speed_factor": 1.0,
    "volume": 1.0
  }' \
  --output test.wav
```

#### 非流式 TTS
```bash
curl -X POST http://localhost:8000/api/tts/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "你好，这是 Zhubo TTS 测试",
    "voice_id": "female_warm_01",
    "speed_factor": 1.0
  }' \
  --output test.wav
```

## 故障排查

### 1. 连接失败
检查 Zhubo TTS 服务是否正常运行：
```bash
curl http://localhost:8765/health
```

### 2. 查看日志
后端日志会显示 TTS 请求和响应信息：
```
INFO: Zhubo TTS request: speaker=female1, text_len=20
INFO: Zhubo TTS synthesized 48000 bytes
```

### 3. 切换回其他 TTS 提供者
修改 `.env` 文件中的 `TTS_PROVIDER`：
```bash
# 切换回 IndexTTS-2
TTS_PROVIDER=idextts2
```

## 技术细节

### 适配器设计
- 使用 `httpx` 库进行 HTTP 请求（与项目其他部分保持一致）
- 同步 API 设计，通过 `asyncio.to_thread` 在异步上下文中调用
- 自动重试和错误处理
- 30 秒请求超时

### 流式处理
- 文本按标点符号分段
- 每段独立合成，逐段返回音频流
- WAV 头只在第一段包含
- 支持客户端提前断开连接

### 并发控制
- 与其他 TTS 提供者共享相同的并发锁和限流机制
- 前台/后台请求优先级管理
- 资源池管理

## 测试

运行集成测试：
```bash
cd backend
python3 test_zhubo_structure.py
```

预期输出：
```
Tests passed: 5/5
✓ Zhubo TTS integration structure is complete!
```
