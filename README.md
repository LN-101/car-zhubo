# car-zhubo

本仓库是「汽车直播智能体」相关工作的发布快照，包含两个互相配合的子项目：一个负责直播话术的流式语音播报，一个是面向汽车销售直播场景的完整智能体。仓库内容是某一时点的代码快照，两个项目各自的提交历史不在本仓库中。

## 目录结构

| 目录 | 内容 |
| --- | --- |
| `zhubo/` | 直播脚本流式播报。使用本机 IndexTTS 2.5 将直播话术分段合成，在整篇音频生成完成之前就开始通过本机音频设备播放；提供中文 WebUI，支持实时改稿与语速／音量／语调控制，并保留原有命令行用法。 |
| `car-live-deployment-v3/` | 汽车直播智能体。面向汽车销售直播场景的本地智能体，包含汽车资料知识库与检索问答、IndexTTS2／GPT-SoVITS 拟人化播报、动态改稿、音色样本管理和 Live2D 数字主播。 |

## 快速开始

### zhubo：流式播报

```bash
cd zhubo
bash run_webui.sh --host 127.0.0.1 --port 7860
```

打开 http://127.0.0.1:7860，输入脚本或上传 UTF-8 TXT 后点击「开始播报」。

命令行方式：

```bash
cd zhubo
bash run_tts.sh --file examples/欧拉5直播脚本.txt
```

完整说明见 `zhubo/README.md`。

### car-live-deployment-v3：直播智能体

在 Windows 上执行：

```powershell
cd car-live-deployment-v3
powershell -ExecutionPolicy Bypass -File .\start.ps1
```

前端 http://127.0.0.1:5173，后端 API http://127.0.0.1:8000。

首次运行前按 `car-live-deployment-v3/backend/.env.example` 创建 `backend/.env`，填写大模型接口（`LLM_BASE_URL`／`LLM_MODEL`／`LLM_API_KEY`）与 TTS 服务地址；已有密钥留空即保留原值。

完整说明见 `car-live-deployment-v3/README.md`、`car-live-deployment-v3/QUICK_START.md` 与 `car-live-deployment-v3/DEPLOYMENT.md`。

## 关于本仓库

- 两个子项目各自保持独立目录结构，只包含各自 Git 已跟踪的源码与文档。
- 模型权重、虚拟环境、运行日志、数据库、上传数据等未跟踪内容不随本仓库分发；运行依赖本机的 IndexTTS、GPT-SoVITS、Live2D 模型等环境，需按各项目文档在本地准备。
- 仓库不包含任何密钥；需要凭据的服务请自行配置本地 `.env`。
