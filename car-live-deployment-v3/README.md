# 汽车直播智能体

面向汽车销售直播场景的本地智能体原型，包含汽车资料知识库、检索问答、IndexTTS2/GPT-SoVITS 拟人化播报、动态改稿、音色样本管理和 Live2D 数字主播。

当前默认使用官方 IndexTTS-2.5；GPT-SoVITS 仍可通过配置切回。2026年9月7日功能完善与三轮复验结果见 [最终赛题验收报告](artifacts/implementation-2026-09-07/最终赛题验收报告.md)，大模型由用户按 [接口说明](docs/LLM_INTEGRATION.md) 自行接入。数字主播仅在本地优化，提交源码ZIP暂未更新。

大模型现在可直接在“模型接口”页面填写地址、模型名和API Key，点击“保存配置”或“保存并测试连接”，无需重启后端。已有密钥留空保留，页面不回显；配置保存后下次启动仍然有效。

## 快速启动

```powershell
cd C:\Users\seele\Desktop\test
powershell -ExecutionPolicy Bypass -File .\start.ps1
```

打开：http://127.0.0.1:5173

如果浏览器显示 `ERR_CONNECTION_REFUSED`，本地服务可能尚未启动或已退出，请双击项目目录里的 `启动汽车直播智能体.cmd`。入口会先打开网页，语音模型在后台预热；重复运行会复用现有进程。未安装下面的开机启动任务时，重启电脑后需要再次启动项目。

也可以双击 `启动汽车直播智能体.cmd`。如需电脑登录后自动启动一次，执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\install-startup.ps1
```

开机登录任务负责拉起本项目的前端、后端和 GPT-SoVITS；如果 Windows 任务注册失败，会自动退回 Startup 文件夹快捷方式。启动脚本带有防重复锁，不会重复启动已经监听的服务；GPT-SoVITS 仍在加载时，页面会先显示可用并自动等待语音服务恢复。移除开机启动：

```powershell
powershell -ExecutionPolicy Bypass -File .\install-startup.ps1 -Remove
```

服务地址：

- 前端：5173
- 后端 API：8000
- IndexTTS-2.5：按 `INDEX_TTS2_URL` 或本地模型配置
- GPT-SoVITS：9880（仅在 `TTS_PROVIDER=gpt-sovits` 时启动）

数字主播

前端的“数字主播”页面会加载 `LIVE2D_MODEL_ROOT` 下的 Live2D Cubism 模型。默认路径是 `C:\\Users\\seele\\Desktop\\原神`，模型文件为 `Hu Tao.model3.json`。页面与直播台共用汽车脚本、RAG 问答和 GPT-SoVITS：可以让胡桃读稿，也可以检索资料后让她回答观众问题；播报时嘴型会随音频能量变化。模型文件通过后端只读白名单路由提供，未复制进代码仓库。

嘴型由独立的 `frontend/lip-sync.js` 根据已排程音频的 20ms 音量包络驱动，使用音频设备输出时钟对齐，保留停顿并平滑开合。模型动画以最高 30 FPS 更新；暂停、停止和改稿会同步暂停、清空或取消对应的嘴型数据，不使用固定频率模拟张嘴。回归测试：`node --test frontend/tests/lip-sync.test.cjs`。

## 语音引擎

默认使用 IndexTTS-2.5，GPT-SoVITS 配置与其相互独立。将以下变量写入 `backend/.env`，二选一：

```dotenv
# 使用独立的 IndexTTS2 HTTP 包装服务
TTS_PROVIDER=idextts2
INDEX_TTS2_URL=http://127.0.0.1:8001
# 可选：没有上传克隆音色时使用的参考音频
# INDEX_TTS2_REF_AUDIO=C:\\path\\to\\speaker.wav

# 或使用本地 IndexTTS2 官方 checkout
# INDEX_TTS2_ROOT=C:\\Users\\seele\\Desktop\\IndexTTS2
# INDEX_TTS2_CONFIG=C:\\Users\\seele\\Desktop\\IndexTTS2\\checkpoints\\config.yaml
# INDEX_TTS2_MODEL_DIR=C:\\Users\\seele\\Desktop\\IndexTTS2\\checkpoints
# INDEX_TTS2_PYTHON=C:\\Users\\seele\\Desktop\\IndexTTS2\\.venv\\Scripts\\python.exe
```

IndexTTS-2.5 的本地推理入口使用官方 `indextts.infer_v2_5.IndexTTS2`，并自动根据中/英/日/西/阿拉伯文本传入 `lang`，用 `duration_factor` 控制语速；HTTP 模式向 `/tts` 发送 `text`、`spk_audio_prompt`、语言和中性情绪向量，并接受 WAV 或 base64 音频返回。若要继续使用 GPT-SoVITS，将 `TTS_PROVIDER` 改为 `gpt-sovits`，其配置仍只读取 `GPT_SOVITS_*` 变量。

> [!IMPORTANT]
> `INDEX_TTS2_CONFIG` 和 `INDEX_TTS2_MODEL_DIR` 必须指向 **2.5** 权重目录：适配器按 `config.yaml` 里的 `version:` 字段选择 `indextts.infer_v2_5` 还是 `indextts.infer_v2`。指向 2.0 目录不会报错，但会静默退回 2.0 引擎，语速控制和多语言前端随之失效（`start.ps1` 会打印警告）。判断方法：`GET http://127.0.0.1:8001/health` 的 `version` 字段应为 `2.5`，`GET /api/tts/status` 的 `provider_label` / `model_version` 也会同步显示真实版本。
>
> 拉取官方 2.5 权重：`powershell -ExecutionPolicy Bypass -File .\scripts\download_indextts25_checkpoints.py`（优先 ModelScope）。核查记录见 [IndexTTS-2.5 切换核查报告](docs/TTS_INDEX_TTS25_SWITCH_AUDIT.md)。

## 已实现功能

- PDF、DOCX、TXT 多文件批量导入，车型元数据管理；DOCX 段落和表格内容均会进入知识库
- 知识片段切分、离线向量检索、来源和相关度展示
- 资料版本记录、替换、删除和版本查询；删除操作不会移除 `data/sample` 示例源文件
- 直播脚本文本输入和 TXT/MD 文件导入
- IndexTTS-2.5 PCM WAV播报：短预缓冲后排程，后续内容持续生成；GPT-SoVITS保持独立文件和配置，可按需切换
- 后端流式接口也会按自然停顿切分长稿，并拼接后续 PCM，直接调用长文本接口同样可以先收到第一段音频
- 按自然停顿短句顺序生成并连续排程，减少句间等待
- 直播台“实时话术”条目表展示每条话术的编号/状态/话术，可在播报中修改待播条目、按编号之后新增、删除条目；已播完的条目禁止修改和删除（条目级改稿要求当前语音引擎按条目流式输出，即 zhubo；GPT-SoVITS/IndexTTS2 等批量引擎下条目按钮禁用，请用“重新同步脚本”）
- 修改正在播报的条目会立即中断该条并从修订文本开头重播，再继续后续条目；修改待播条目就地替换、不打断当前播放；被替换文本已合成但尚未播出的音频会被丢弃
- 整段“重新同步脚本”按当前条目列表做差异应用（只改待播条目，触及已播条目会被拒绝）
- 语速、音量、语调调节
- GPT-SoVITS v2ProPlus 音色样本上传、参考文本校验与引用音频管理（参考文本为必填，以提升克隆一致性）；新克隆音色使用 v2ProPlus 通用零样本权重，并联合校准声纹相似度与语气稳定性；昔涟按音色记录切换到 GPT-e10 + SoVITS-e6 微调权重，避免不同音色互相污染
- 快速克隆支持样本预检、上传进度、参考文本密度提示和后台预热；参考音频只裁掉明显首尾空白，不重排内部停顿，对过低/过高峰值做有限增益和 3 dB 余量保护，并转为 24kHz 单声道 16-bit PCM WAV，界面展示时长、有效人声比例、静音比例、响度和削波诊断，可一键使用或试听
- 快速克隆支持“麦克风录制”模式：页面提供固定朗读文案，录音最长 10 秒，可回听和重录；浏览器把录音转换为 24kHz 单声道 WAV，并自动将朗读文案作为参考文本提交，避免音频与文字不一致
- 内置三套固定汽车主播声音：“沉稳阿川”“温婉小梅”“亲切阿诚”。内置音色、我的克隆和系统声音分组显示；内置音色资源随项目保存，可直接试听和使用，不依赖用户先上传样本
- 低质量、格式异常或缺少参考文本的克隆音色会标记为“建议优化”且禁止播报，避免影响直播稳定性
- 车型问答文字输出和回答语音播报
- 可选 OpenAI 兼容大模型增强问答；未配置时自动使用本地可复现抽取式 RAG 回退
- 检索准确率、最终问答准确率与 TTS 延迟测试页面
- TTS 单模型推理锁，避免预热、验证、试听和直播并发时触发 GPT-SoVITS 的并发推理限制

## 验收接口

- `POST /api/tests/retrieval`
- `POST /api/tests/qa`
- `POST /api/tests/tts`
- `GET /api/documents/{id}/versions`
- `POST /api/voices/clone`
- `POST /api/voices/analyze`
- `POST /api/voices/{voice_id}/optimize`

详细验收结果见 `docs/ACCEPTANCE.md`。

参赛交付、现场演示、数据合规和主观评测模板见：

- `docs/COMPETITION_SUBMISSION.md`
- `docs/DEMO_RUNBOOK.md`
- `docs/VOICE_EVALUATION.md`

可用 `powershell -ExecutionPolicy Bypass -File .\verify.ps1` 一键复现实验结果。
# 2026-09-07 功能更新

新增批量资料修改/删除、持久化向量与脱敏、完整来源展开、直播统计、真实听测及导出、大模型连接接口。使用方法见 [功能说明](docs/FEATURES_2026-09-07.md)，自行接入大模型见 [接口说明](docs/LLM_INTEGRATION.md)。数字主播在本地继续优化；本轮暂未重新打包提交源码 ZIP。

## 2026-09-08 语义 RAG 更新

新增 BGE 中文 Embedding、FAISS持久化索引、BM25混合召回、RRF融合、独立BGE重排、参数／FAQ父子分块、动力范围与资料冲突检查。首次部署须运行 `scripts/setup_rag_models.py` 下载模型。页面“知识库 → 检索索引与资料检查”可查看完整链路。

模型选择、接口与测试方法见 [RAG方案](docs/RAG_PIPELINE.md)，本轮验收见 [RAG验收报告](artifacts/rag-upgrade-2026-09-08/验收报告.md)。
