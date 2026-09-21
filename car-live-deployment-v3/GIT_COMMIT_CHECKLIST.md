# Git 提交清单

## 准备提交的文件

### 新增文件
```bash
git add backend/app/tts/adapters/zhubo_adapter.py
git add backend/test_zhubo_structure.py
git add ZHUBO_TTS_INTEGRATION.md
git add INTEGRATION_SUMMARY.md
git add verify_integration.sh
```

### 修改文件
```bash
git add backend/app/config.py
git add backend/app/main.py
git add backend/.env.example
```

## 建议的提交信息

```
feat: 集成 Zhubo TTS 服务支持

- 新增 ZhuboTTSAdapter 适配器 (backend/app/tts/adapters/zhubo_adapter.py)
- 在 config.py 中添加 zhubo_tts_url 配置项
- 在 main.py 中集成 zhubo TTS 提供者
- 更新 .env.example 添加 Zhubo 配置示例
- 支持流式和非流式 TTS 合成
- 自动映射 voice_id 到 Zhubo speaker 格式
- 添加健康检查和错误处理
- 添加集成文档和测试脚本

Features:
- 流式 TTS: POST /api/tts/stream
- 非流式 TTS: POST /api/tts/synthesize
- 健康检查: Zhubo 服务状态检测
- Voice ID 映射: 自动转换到 Zhubo 格式
- 并发控制: 与现有 TTS 提供者共享
- 优先级管理: 前台/后台请求分离

Configuration:
TTS_PROVIDER=zhubo
ZHUBO_TTS_URL=http://localhost:8765

Documentation:
- ZHUBO_TTS_INTEGRATION.md: 完整集成说明
- INTEGRATION_SUMMARY.md: 修改总结
- verify_integration.sh: 自动化验证脚本
```

## 提交命令

```bash
# 查看修改
git status

# 添加所有相关文件
git add backend/app/tts/adapters/zhubo_adapter.py \
        backend/app/config.py \
        backend/app/main.py \
        backend/.env.example \
        backend/test_zhubo_structure.py \
        ZHUBO_TTS_INTEGRATION.md \
        INTEGRATION_SUMMARY.md \
        verify_integration.sh

# 查看暂存的更改
git diff --cached

# 提交
git commit -m "feat: 集成 Zhubo TTS 服务支持

- 新增 ZhuboTTSAdapter 适配器
- 支持流式和非流式 TTS 合成
- 自动 voice_id 映射
- 完整的健康检查和错误处理
- 添加集成文档和测试脚本"

# 推送到远程仓库
git push origin main
```

## 可选：创建分支

如果需要在单独的分支中进行集成：

```bash
# 创建并切换到新分支
git checkout -b feature/zhubo-tts-integration

# 添加和提交文件（同上）
git add ...
git commit -m "..."

# 推送分支
git push origin feature/zhubo-tts-integration

# 在 GitHub 上创建 Pull Request
```

## 验证提交

提交前确保：
1. ✓ 所有测试通过 (`./verify_integration.sh`)
2. ✓ 代码语法正确
3. ✓ 文档完整
4. ✓ 配置示例正确
5. ✓ 不包含敏感信息（密钥、密码等）

## 忽略的文件

以下文件用于本地测试，不需要提交：
- `backend/test_zhubo_adapter.py` (独立测试，可选)
- `backend/test_zhubo_integration.py` (独立测试，可选)
- `backend/.env` (本地配置，已在 .gitignore 中)
