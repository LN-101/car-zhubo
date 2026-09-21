# 直播脚本流式播报

使用本机 IndexTTS 2.5，将直播话术分段合成，在整篇音频生成完成前开始通过本机默认音频设备播放。支持中文 WebUI 实时改稿与语速/音量/语调控制；原有非交互 CLI 继续可用。

## 直播 WebUI

```bash
bash run_webui.sh --host 127.0.0.1 --port 7860
```

模型加载并预热一次后，打开 `http://127.0.0.1:7860`。输入脚本或上传 UTF-8 TXT（已选文件优先），可上传 WAV 参考音色；点击“开始播报”，声音从**服务器本机音频设备**播放。播报结束后服务保持运行，下一轮复用模型。参考音色在下一轮开始时生效。

话术按自然标点切分为带稳定编号的列表，点选一行可填写修改内容，也可用编号操作：

- 修改正在播放的话术：中断并从修订文本开头重播，之后继续下一项。
- 已经播完的话术禁止修改或删除（播报结束后同样生效）。点击已播行或提交修改、删除时弹窗提示，请在后续待播条目中修改，或新增话术。
- 修改待播项或添加话术：不打断当前播放，按列表顺序播出。新增位置用“此编号之后”指定，0 为末尾；放在已播位置的新增项在当前项之后播出。
- 删除当前项：中断并转下一项；删除待播项会丢弃其音频。
- 停止：立即取消后续播放；已经执行的 GPU 推理结束后可开始下一轮。

语速范围 0.5–2 倍，映射到模型的时长系数 `1 / speed`；音量 0–200%，立即作用于后续设备回调并对 PCM16 削波。自然/亲切/活力/沉稳语调配合 0–1 强度控制情绪向量。语速、语调从下一生成片段生效，已排队音频保留原值。参数沿用到下一轮。

实时指标面板显示首音延迟、欠载、每次编辑的响应时间和实际生成参数。每轮完成或停止后，在 `outputs/webui/时间戳/` 保存 `metrics.json` 和 `playback.wav`，可通过 `--output` 更改父目录。WAV 记录设备回调输出，包含音量效果，以及已开始输出后的队列缺音静音。采样位置指软件提交给设备的 PCM；设备已接收的低延迟缓冲不能撤回，控制在下一回调生效。

内存待播 PCM 上限为 3 段。被新增项挤后的音频保存到会话临时文件，按原采样偏移恢复，保留生成时的参数；磁盘读取由合成工作线程完成。临时文件在会话结束时关闭。整轮录音仍保存在内存中，随播报长度增长。

## 运行

在 `/home/ln/AI/zhubo` 执行：

```bash
bash run_tts.sh --file examples/欧拉5直播脚本.txt
bash run_tts.sh --text '欢迎来到直播间。今天我们来聊聊欧拉五纯电版。'
```

按 Ctrl+C 终止播报。默认使用 `/home/ln/AI/index-tts/examples/voice_01.wav`，通过 `--voice /绝对路径/参考音频.wav` 替换。文件输入支持 UTF-8 TXT。

首次启动需要加载模型并预热，之后才开始计时并播报。CLI 每次启动都会重新加载；同一进程内 `--runs 2` 可重复播报、复用模型和参考音色缓存。WebUI 则在整个服务进程中复用模型。

```bash
bash run_tts.sh --file examples/欧拉5直播脚本.txt --runs 2 --output outputs/optimized
```

输出目录包含每轮的 `run-N.wav` 和 `metrics.json`。WAV 保存的是合成音频，不包含播放欠载时设备补出的静音；实际欠载另记在 JSON 中。

## 环境

- 已有 `/home/ln/AI/index-tts/.venv`、IndexTTS 2.5 权重与辅助权重。
- CUDA GPU，本机使用 BF16、单 beam、4 个 CPU 线程；不加载情绪文本模型。
- 增量依赖：`uv pip install --python /home/ln/AI/index-tts/.venv/bin/python -r requirements.txt`。
- Linux PortAudio：系统包 `libportaudio2`。本机缺少该包，已将 Ubuntu 软件源中的包解压至 `.local`，启动脚本会加载该目录。该目录不纳入版本管理。

没有管理员权限时可在本机 Ubuntu 环境重建本地库：

```bash
mkdir -p .local/packages
cd .local/packages
apt-get download libportaudio2
dpkg-deb -x libportaudio2_*.deb ..
ln -sf libportaudio.so.2.0.0 ../usr/lib/x86_64-linux-gnu/libportaudio.so
cd ../..
```

## 测量口径

- `initialization_s`：模型构造与加载，不含此前 Python 导入耗时。
- `warmup_s`：模型加载后合成一次短句，不播放、不复用其音频。
- `first_pcm_s`：本轮请求开始至首块 PCM 可用，包含设备打开时间。
- `first_device_output_s`：由 PortAudio 回调的 DAC 时间戳估计首块输出时间，不是麦克风测得的物理首音。
- `rtf`：实际生成耗时 / 合成音频时长，排除等待播放队列空位的时间；小于 1 表示平均生成速度快于播放速度。
- `underrun_events` / `underrun_s`：已经开始播报但后续音频尚未生成时的缺音次数与时长。
- `device_underflows`：音频驱动回调报告的欠载次数，与应用队列缺音分别统计。

逐段流式不同于单句内部逐 token 输出：每个文本段的音频完整生成后，立即入播放队列。短首段及短第二段降低启动等待，后续段最大 32 字符；队列最多容纳 3 块 PCM。当前保留本轮音频用于 WAV 输出，内存随脚本长度增长。

## 验证

```bash
LD_LIBRARY_PATH="$PWD/.local/usr/lib/x86_64-linux-gnu" \
  /home/ln/AI/index-tts/.venv/bin/python -m unittest discover -s tests -v
```

测试覆盖顺序播放、跨片段填充、欠载统计、取消、实时编辑、已播条目保护、生成中的过期音频及参数生效。首轮 CLI 实测见 `docs/第一步延迟测试报告.md`，WebUI 实测见 `docs/实时改稿测试报告.md`。

本次不实现 RAG、音色克隆或预设管理。样本文案取自 `资源` 中的车型信息，避开其中不一致的价格与优惠数据；本项目不核验汽车业务事实。
