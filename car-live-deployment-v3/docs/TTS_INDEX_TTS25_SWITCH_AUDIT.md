# 语音合成链路 IndexTTS-2.5 切换核查报告

核查日期：2026-09-10
核查范围：`TTS_PROVIDER` 路由、后端适配器、HTTP 包装服务、本地模型权重、启动脚本、状态接口、前端标签、验收指标
对照基线：官方仓库 <https://github.com/index-tts/index-tts/blob/main/docs/README_zh.md>，以及 IndexTeam/IndexTTS-2.5、IndexTeam/IndexTTS-2 两个官方模型仓库

## 结论

**没有完成切换。** 服务提供方（provider）已经切到 `idextts2`，推理链路、锁定、预热、流式接口也确实全部走 IndexTTS 适配器；**但实际加载的模型权重是 IndexTTS-2.0，不是 IndexTTS-2.5。**

也就是说：链路是通的，模型是旧的，界面和接口却把它标成了 2.5。同时项目自带的 TTS 验收在 2.0 权重上已经不达标。

## 一、已真正切换的部分

| 环节 | 状态 | 证据 |
| --- | --- | --- |
| provider 选择 | ✅ 已切换 | `backend/.env:7` `TTS_PROVIDER=idextts2`；`backend/.env.example:6` 同值 |
| 后端路由 | ✅ 已切换 | `backend/app/main.py` 中 `synthesize`/`stream`/warmup/克隆验收/`/api/tests/tts` 均有 `idextts2` 分支 |
| 启动脚本 | ✅ 已切换 | `start.ps1:89-100` 仅在 `TTS_PROVIDER=idextts2` 时拉起 8001 包装服务，并跳过 GPT-SoVITS 9880 |
| 适配器隔离 | ✅ 已实现 | `backend/app/tts_idextts2.py` 独立文件，GPT-SoVITS 配置互不干扰 |
| 运行时连通 | ✅ 正常 | `GET /api/tts/status` → `ready:true, mode:"http", endpoint:"http://127.0.0.1:8001"`；实测合成返回 200、`audio/wav`、22050 Hz 单声道 16-bit |

## 二、关键问题：跑的是 IndexTTS-2.0

本地模型目录：`C:\Users\seele\Desktop\IndexTTS2\checkpoints`（`INDEX_TTS2_MODEL_DIR`）。

| 校验项 | 本地值 | 官方 2.0 | 官方 2.5 | 判定 |
| --- | --- | --- | --- | --- |
| `config.yaml` git blob | `98d16c38…4dd84e` | `98d16c38…4dd84e` | `b3f15b22…54e203` | **与 2.0 逐字节相同** |
| `config.yaml` 大小 | 2882 | 2882 | 2860 | 2.0 |
| `gpt.pth` 大小 | 3484663079 | 3484663079 | 3259599833 | 2.0 |
| `s2mel.pth` 大小 | 1202198223 | 1202198223 | 414908601 | 2.0 |
| `bpe.model` | 475997 | 475997 | 2.5 仓库无此文件 | 2.0 |
| `config.yaml` 内 `version:` | `2.0` | `2.0` | `2.5` | 2.0 |
| `config.yaml` 内 `number_text_tokens` | 12000 | 12000 | 60509 | 2.0 |
| `config.yaml` 内 `vocoder.name` | `nvidia/bigvgan_v2_22khz_80band_256x` | 同左 | `bigvgan_generator.pt` | 2.0 |
| `gpt.pth` 内 `text_embedding.weight` | `(12001, 1280)` | 12000 token | 60509 token | 2.0 |
| `codec.pth` | 607290935 | 2.0 仓库无此文件 | 607290935 | **2.5 残留** |
| `checkpoints_2` / 2.5 模型目录 | 不存在 | — | — | 缺失 |

补充证据：

- 运行中的 8001 服务自报版本：`GET http://127.0.0.1:8001/health` → `{"status":"ok","model_loaded":true,"device":"cuda:0","version":"2"}`。
- `backend/app/tts_idextts2.py:55-70` 与 `IndexTTS2/index_tts2_server.py:22-38` 都按 `config.yaml` 的 `version:` 字段选模块；读到 `2.0` 即 `import indextts.infer_v2`，2.5 的 `indextts.infer_v2_5` 从未被加载。

**成因判断**：该目录是一次「2.0 覆盖 + 2.5 部分下载」的混合安装。`codec.pth` 来自 2.5 仓库，但 2.5 的核心权重（`gpt.pth`、`s2mel.pth`）和 `config.yaml` 仍是 2.0 的，说明 2.5 下载未完成或旧文件未被覆盖，随后版本探测正确地退回了 2.0。这也解释了为什么没有出现代码注释里警告的「2.0 权重配 2.5 前端 → CUDA device-side assert」崩溃。

**副作用**：`codec.pth` 在当前 2.0 路径下不会被加载（2.0 走 `build_semantic_codec` + `hf_cache/semantic_codec_model.safetensors`），属于无效占用。

## 三、因此被静默关掉的能力

这些是 2.5 独有、当前完全没生效的功能：

1. **语速控制失效。** 适配器与包装服务只在 `version == "2.5"` 时才传 `duration_factor`（`tts_idextts2.py:181-185`、`index_tts2_server.py:102-106`）。2.0 的 `infer()` 没有该参数，请求里的 `duration_factor`/`speed_factor` 被直接丢弃 → 前端语速滑块对实际输出无影响。
2. **语言条件不生效。** 2.0 路径不传 `lang`。
3. **西语 / 阿拉伯语不支持。** 2.5 官方支持 zh/en/ja/es/ar，但 `_language_for_text` 只区分日文假名、中文、其余一律 `EN`（`tts_idextts2.py:201-207`、`index_tts2_server.py:121-127`）。
4. **拼音 / CMU 音素 / 日语假名发音控制**（2.5 新特性）无入口。

## 四、即使装上 2.5 权重，仍然存在的代码缺陷

**`lang` 取值错误（日文会静默降级）。** 两个文件都返回 `"JP"`：

- `backend/app/tts_idextts2.py:204` → `return "JP"`
- `C:\Users\seele\Desktop\IndexTTS2\index_tts2_server.py:124` → `return "JP"`

而官方 `indextts/utils/tokenizer.py:19` 的 `LANGUAGES` 键是 `"ja": "japanese"`，`LANGUAGE_DICT` 中没有 `jp`；`lang_to_token()`（同文件 173-177 行）在找不到键时**不报错，静默回退到 `"common"`**。因此日文合成在 2.5 下会丢失语言条件。正确值应为 `"ja"`。

## 五、验收与指标问题

在**当前** 2.0 部署上实测（`POST /api/tests/tts`，克隆音色 `voice-a58847fe6169`）：

```
first_audio_ms = [15858.5, 21222.0, 20176.1]   average = 19085.5
meets_target = false                           目标 = 3000 ms
```

单句合成实测（`/api/tts/synthesize`，`voice-ff9f6ad7787d`）：

| 轮次 | 总耗时 | 音频时长 | RTF |
| --- | --- | --- | --- |
| 1 | 14826 ms | 1.70 s | 8.7 |
| 2 | 11739 ms | 1.81 s | 6.5 |
| 3 | 13996 ms | 2.25 s | 6.2 |
| 4 | 12192 ms | 0.93 s | 13.1 |

两点结论：

- 官方 2.5 在 RTX 4090 上是 RTF ≈ 0.20，2.0 fp16 是 ≈ 0.33。**当前 RTF 6～13，比两个官方数字都差一到两个数量级**，与本机历史 GPT-SoVITS 验收（约 1.2～2.7 s）也是明显回退。需要单独排查（权重版本、bf16/fp16 未启用、CUDA kernel/显存调度、逐句重复建会话等）。
- 指标本身也有偏差：`main.py:3184` 用**整段合成**的耗时填进 `first_audio_ms`，对 HTTP 模式并非「首个可播放 PCM」延迟，与 `verify.ps1` 里 `tts_scope` 的声明不一致。

`verify.ps1` 会因 `meets_target = false` 直接抛出「项目自测未通过」。

## 六、标识与文档不一致

代码把当前引擎一律标为 2.5，与实际不符：

- `backend/app/tts_idextts2.py:31` `label = "IndexTTS-2.5"`
- `backend/app/main.py:645` `"provider_label": "IndexTTS-2.5"`
- `frontend/app.js:28` 兜底文案 `'IndexTTS-2.5'`
- `GET /api/tts/status` 返回里**没有任何真实模型版本字段**，无法从接口判断跑的是 2.0 还是 2.5

文档自相矛盾：

| 文件 | 说法 | 与实际关系 |
| --- | --- | --- |
| `README.md:5,47` | 「当前默认使用官方 IndexTTS-2.5」 | ❌ 实际 2.0 |
| `docs/TTS_MIGRATION_ASSESSMENT.md:12,83` | 「默认保持 `TTS_PROVIDER=gpt-sovits`」「IndexTTS2 作为独立实验入口」 | ❌ 已过期 |
| `docs/DEMO_RUNBOOK.md:10`、`docs/FEATURES_2026-09-07.md:17` | 「IndexTTS2 保持独立、未切换启用」 | ❌ 已过期 |
| `artifacts/acceptance-2026-09-07/*` | GPT-SoVITS 时期数据 | ❌ 无 idextts2 验收 |

其他遗留：

- `backend/app/config.py:24` 代码默认仍是 `tts_provider = "gpt-sovits"`，而 `main.py:120` 在空值时又默认按 `idextts2` 处理 —— 两处默认值相反，只有 `.env` 让实际值偏向 idextts2。
- `backend/app/preset_voices.py:24` 把内置音色的 `provider` 硬编码为 `'gpt-sovits'`；`frontend/app.js:452` 也按 `dataset.provider === 'gpt-sovits'` 判断，语义已名不副实（当前靠其它条件兜住，未暴露故障）。
- 包装服务 `index_tts2_server.py` **位于仓库之外**（`C:\Users\seele\Desktop\IndexTTS2\`）。提交源码 ZIP 不含该文件，链路不自洽、不可复现。

## 七、要真正切换到 2.5 的动作清单

1. **补齐 2.5 权重**（不要覆盖现有 2.0 目录，保留回退能力）：

   ```powershell
   cd C:\Users\seele\Desktop\IndexTTS2
   uv tool install "huggingface-hub"
   hf download IndexTeam/IndexTTS-2.5 --local-dir checkpoints_2_5
   ```

   预期：`gpt.pth` 3259599833、`s2mel.pth` 414908601、`config.yaml` 2860、`codec.pth` 607290935。
2. 把 `backend/.env` 的 `INDEX_TTS2_CONFIG` / `INDEX_TTS2_MODEL_DIR` 指向 `checkpoints_2_5`，重启 8001。
3. 校验：`GET http://127.0.0.1:8001/health` 必须返回 `"version": "2.5"`；`config.yaml` 的 `version:` 为 `2.5`、`number_text_tokens` 为 `60509`。（`use_bf16` 已由现有代码在 2.5 分支自动启用。）
4. 修复 `lang`：`tts_idextts2.py` 与 `index_tts2_server.py` 的 `"JP"` 改为 `"ja"`，并补上 `es`/`ar` 检测（至少在文本含西里尔/阿拉伯字符集时给出对应值）。
5. 把 `index_tts2_server.py` 移入仓库（如 `scripts/`），`start.ps1` 改指仓库内路径。
6. 让 `provider_label` 与 `/api/tts/status` 反映真实版本（例如读 8001 `/health` 的 `version` 字段），去掉三处硬编码的「IndexTTS-2.5」。
7. 统一 `config.py` 与 `main.py` 的默认 provider。
8. 修正 `docs/` 中已过期的默认引擎描述，并把 `artifacts` 补齐为 idextts2 实测数据。
9. 重跑 2.5 的首包延迟与音质验收（当前 RTF 6～13 必须先定位原因）。

## 附：本次核查用到的命令

```powershell
# 运行中服务自报版本（判定 2.0 的直接证据）
Invoke-RestMethod http://127.0.0.1:8001/health

# config.yaml 与官方发布比对（git blob 哈希）
# 本地 = 98d16c3892bd2321e7da71a379ecc8e1fa4dd84e = 官方 IndexTTS-2
# 官方 IndexTTS-2.5 = b3f15b22f394f2327de574e9b5801c1d9654e203

# 权重内部 token 表大小（2.0 = 12000，2.5 = 60509）
# torch.load('checkpoints/gpt.pth', mmap=True, weights_only=True)['text_embedding.weight'].shape
# -> torch.Size([12001, 1280])

# 项目自带验收
Invoke-RestMethod http://127.0.0.1:8000/api/tests/tts -Method Post
```

---

## 整改记录（2026-09-10）

### 已完成并验证

| # | 本文前述问题 | 处理 | 验证证据 |
| --- | --- | --- | --- |
| 1 | 实际加载 2.0 权重却对外标称 2.5 | 下载官方 2.5 权重到 `checkpoints_2_5`，`backend/.env` 改指该目录 | `GET :8001/health` → `version:"2.5"`；`config.yaml` blob = `b3f15b22…54e203`（官方 2.5）；8 个文件大小与官方逐字节一致 |
| 2 | `lang` 日文码写作 `JP`，官方键为 `ja`，未知码静默回退 `common` | 改为 `ja`，并补齐 `es` / `ar` 检测；后端适配器与包装服务同步 | `scripts/verify_indextts25_switch.py` 全部通过（含 5 语种用例） |
| 3 | 2.0 下 `duration_factor` 被静默丢弃 | 上报真实版本，`/api/tts/status` 新增 `model_version` 与 `speed_control` | 现返回 `"model_version":"2.5","speed_control":true` |
| 4 | `provider_label` 硬编码 `IndexTTS-2.5` | 由引擎探测的真实版本生成标签 | 指向 2.0 时显示 `IndexTTS-2.0`，指向 2.5 时显示 `IndexTTS-2.5` |
| 5 | 包装服务 `index_tts2_server.py` 位于仓库之外 | 收录到 `scripts/index_tts2_server.py`，`start.ps1` 改指仓库内路径 | 提交源码可自洽运行 |
| 6 | `config.py` 代码默认值（gpt-sovits）与 README / `.env.example` 相反 | 代码默认值改为 `idextts2`，与 `main._tts_provider()` 的空值回退一致 | 三处默认值统一 |
| 7 | 指向 2.0 权重时无任何提示 | `start.ps1` 读取 `config.yaml` 的 `version:`，低于 2.5 时 `Write-Warning` | — |
| 8 | 缺少切换诊断手段 | 新增 `scripts/verify_indextts25_switch.py`（版本/语种/语速映射/在线状态）与 `scripts/download_indextts25_checkpoints.py`（ModelScope 直连下载，可断点续传） | `verify_indextts25_switch.py` 输出 `ALL CHECKS PASSED` |

补充修复：包装服务改为从 `--model-dir` 推导 IndexTTS checkout 并写入 `sys.path`。此前它依赖 `INDEX_TTS2_ROOT` 环境变量，而该变量只存在于 `backend/.env`，直接启动会 `ModuleNotFoundError: No module named 'indextts'`——这正是本次切换过程中服务一度起不来的原因。

### 仍未解决

- **推理性能没有随 2.5 改善**。2.5 就绪后（BF16，`use_cuda_kernel=False`、`use_deepspeed=False`、`use_qwen_emo=False`）实测单句合成 RTF 为 **2.9–4.3**，冷启动首句 9.2；官方 RTX 4090 参考值为 0.21（2.5 bf16）。本机为 RTX 4060 Laptop（8 GB），且与 QQ、Edge GameAssist 等共享 GPU。需单独排查显存压力、batch 与首包策略，本文前述的 ≤3 秒首包目标尚未复测通过。
- `qwen0.6bemo4-merge`（约 1.2 GB）未下载：`use_qwen_emo=False` 时不会加载；若后续需要 `use_emo_text` 文本情感控制再补齐。
- `/api/tests/tts` 仍以**整段合成耗时**填 `first_audio_ms`，HTTP 模式下并非「首个可播放 PCM」延迟，指标口径需要修正后再作为验收依据。
