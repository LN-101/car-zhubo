# Zhubo TTS 集成 - 修改总结

## 完成的工作

### 1. 创建 Zhubo TTS 适配器
**文件**: `backend/app/tts/adapters/zhubo_adapter.py`

功能：
- 实现 `ZhuboTTSAdapter` 类
- 提供 `synthesize()` 方法进行语音合成
- 提供 `health_check()` 方法检查服务健康状态
- 实现 `_map_voice_id()` 方法映射 voice_id 到 Zhubo speaker 格式
- 使用 `httpx` 库（与项目保持一致）
- 30 秒超时，完善的错误处理

### 2. 修改配置文件
**文件**: `backend/app/config.py`

添加内容：
```python
zhubo_tts_url: str = "http://localhost:8765"
```

### 3. 集成到主应用
**文件**: `backend/app/main.py`

修改内容：
- 导入 `ZhuboTTSAdapter`
- 添加全局变量 `_zhubo_adapter`
- 实现 `_get_zhubo_adapter()` 函数初始化适配器
- 在 `_tts_provider()` 中添加 "zhubo" 选项
- 在流式 TTS 端点中添加 zhubo 分支处理
- 在非流式 TTS 端点中添加 zhubo 分支处理

### 4. 更新环境变量示例
**文件**: `backend/.env.example`

添加内容：
```bash
# Zhubo TTS HTTP Service Endpoint
# When TTS_PROVIDER=zhubo, configure the Zhubo service URL here
ZHUBO_TTS_URL=http://localhost:8765
```

### 5. 创建文档
**文件**: `ZHUBO_TTS_INTEGRATION.md`
- 集成说明
- 配置方法
- API 要求
- 使用示例
- 故障排查

### 6. 创建测试脚本
**文件**: `backend/test_zhubo_structure.py`
- 语法检查
- 结构验证
- 集成完整性测试

## 使用说明

### 快速开始

1. **配置环境变量**
   ```bash
   cd backend
   cp .env.example .env
   # 编辑 .env 文件
   ```

2. **设置 TTS 提供者**
   ```bash
   # 在 .env 中设置
   TTS_PROVIDER=zhubo
   ZHUBO_TTS_URL=http://localhost:8765
   ```

3. **启动服务**
   ```bash
   # 确保 Zhubo TTS 服务已运行
   # 启动 car-live-deployment-v3
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

4. **测试**
   ```bash
   curl -X POST http://localhost:8000/api/tts/stream \
     -H "Content-Type: application/json" \
     -d '{"text": "测试", "voice_id": "female_warm_01"}' \
     --output test.wav
   ```

## API 兼容性

### Zhubo TTS 服务需要提供的端点：

1. **健康检查**: `GET /health` → 200 OK
2. **语音合成**: `POST /tts/synthesize`
   ```json
   {
     "text": "文本内容",
     "speaker": "female1",
     "speed": 1.0,
     "tone": "neutral",
     "intensity": 0.3,
     "volume": 1.0
   }
   ```
   返回：WAV 格式音频二进制数据

## 特性

✅ 流式 TTS 支持  
✅ 非流式 TTS 支持  
✅ 自动 voice_id 映射  
✅ 完整的错误处理  
✅ 健康检查支持  
✅ 与现有 TTS 提供者无缝切换  
✅ 共享并发控制机制  
✅ 前台/后台请求优先级管理  

## 测试结果

```bash
$ python3 test_zhubo_structure.py
Testing Zhubo TTS Integration (Structure)
==================================================

Syntax Check
--------------------------------------------------
✓ Syntax valid: app/tts/adapters/zhubo_adapter.py
✓ Syntax valid: app/main.py
✓ Syntax valid: app/config.py

Adapter Structure
--------------------------------------------------
✓ Found: class ZhuboTTSAdapter
✓ Found: def synthesize(
✓ Found: def health_check(
✓ Found: def _map_voice_id(
✓ Found: import httpx

Config Structure
--------------------------------------------------
✓ Found in config: zhubo_tts_url
✓ Found in config: http://localhost:8765

Main Integration
--------------------------------------------------
✓ Found in main.py: ZhuboTTSAdapter
✓ Found in main.py: _zhubo_adapter
✓ Found in main.py: def _get_zhubo_adapter()
✓ Found in main.py: if provider == "zhubo":

Environment Example
--------------------------------------------------
✓ Found in .env.example: ZHUBO_TTS_URL
✓ Found in .env.example: TTS_PROVIDER

==================================================
Tests passed: 5/5

✓ Zhubo TTS integration structure is complete!
```

## 文件清单

### 新增文件
- `backend/app/tts/adapters/zhubo_adapter.py` - Zhubo TTS 适配器
- `backend/test_zhubo_structure.py` - 结构测试脚本
- `ZHUBO_TTS_INTEGRATION.md` - 集成文档

### 修改文件
- `backend/app/config.py` - 添加 zhubo_tts_url 配置
- `backend/app/main.py` - 集成 Zhubo TTS 支持
- `backend/.env.example` - 添加配置示例

## 下一步

集成已完成，可以：
1. 启动 Zhubo TTS 服务
2. 配置 car-live-deployment-v3 使用 zhubo 提供者
3. 测试语音合成功能
4. 根据需要调整 voice_id 映射关系

如有问题，请参考 `ZHUBO_TTS_INTEGRATION.md` 文档中的故障排查部分。
