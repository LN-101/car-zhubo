"""Chinese broadcast controls; audio plays on the server's local device."""
import argparse
from datetime import datetime
from pathlib import Path
from threading import Lock

import gradio as gr

from .engine import Engine, Parameters
from .session import Session


class Controller:
    def __init__(self, engine, output):
        self.engine = engine
        self.output = Path(output).resolve()
        self.parameters = Parameters()
        self.session = None
        self.lock = Lock()

    def start(self, text, script_file=None, voice=None):
        if script_file:
            text = Path(script_file).read_text(encoding="utf-8")
        with self.lock:
            if self.session and self.session.worker.is_alive():
                raise ValueError("上一轮仍在播放或停止中，请稍后重试")
            output = self.output / datetime.now().strftime("%Y%m%d-%H%M%S-%f")
            self.session = Session(text, self.engine.synthesize, voice or self.engine.voice,
                                   self.parameters, output, self.engine.info).start()
        return "已开始播报"

    def stop(self):
        with self.lock:
            if self.session:
                self.session.stop()
        return "已停止播放，正在结束当前合成任务"

    def parameters_changed(self, speed, volume, tone, intensity):
        parameters = Parameters(speed, volume, tone, intensity)
        with self.lock:
            self.parameters = parameters
            if self.session:
                self.session.set_parameters(parameters)
        return parameters.values()

    def edit(self, item_id, text):
        with self.lock:
            if not self.session:
                raise ValueError("请先开始播报")
            self.session.edit(item_id, text)
        return "已修改话术"

    def select(self, item_id):
        with self.lock:
            if not self.session:
                raise ValueError("请先开始播报")
            return int(item_id), self.session.editable_text(item_id)

    def add(self, text, after_id):
        with self.lock:
            if not self.session:
                raise ValueError("请先开始播报")
            item_id = self.session.add(text, after_id or None)
        return f"已添加话术 #{item_id}"

    def delete(self, item_id):
        with self.lock:
            if not self.session:
                raise ValueError("请先开始播报")
            self.session.delete(item_id)
        return "已删除话术"

    def snapshot(self):
        with self.lock:
            return self.session.snapshot() if self.session else {"state": "idle", "items": [],
                                                               "parameters": self.parameters.values()}


def create_app(controller):
    def action(fn):
        def call(*args):
            try:
                return fn(*args)
            except (ValueError, StopIteration, OSError) as error:
                raise gr.Error(str(error) or "话术编号不存在") from error
        return call

    def refresh():
        data = controller.snapshot()
        rows = [[i["id"], i["status"], i["text"]] for i in data["items"]]
        labels = {"idle": "待机", "running": "播报中", "finished": "已完成",
                  "stopped": "已停止", "error": "出错"}
        status = labels[data["state"]]
        if data.get("error"):
            status += "：" + data["error"]
        return rows, status, data

    with gr.Blocks(title="IndexTTS 直播播报", theme=gr.themes.Soft()) as app:
        gr.Markdown("# IndexTTS 直播播报\n音频通过服务器本机音响播放。模型已加载，可连续发起播报。")
        with gr.Row():
            with gr.Column(scale=2):
                text = gr.Textbox(label="直播脚本", lines=6, placeholder="输入直播话术，按自然标点分段…")
                script_file = gr.File(label="上传 UTF-8 文本（选择文件时优先使用文件内容）", file_types=[".txt"], type="filepath")
            with gr.Column():
                voice = gr.Audio(label="参考音色（留空使用默认；下一轮生效）", type="filepath", sources=["upload"], format="wav")
                with gr.Row():
                    start = gr.Button("开始播报", variant="primary")
                    stop = gr.Button("停止播报", variant="stop")
                message = gr.Textbox(label="操作结果", interactive=False)
                status = gr.Textbox(label="播报状态", value="待机", interactive=False)
        with gr.Group():
            gr.Markdown("### 播报参数\n音量立即生效；语速和语调从下一生成片段生效。")
            with gr.Row():
                speed = gr.Slider(0.5, 2, value=1, step=0.05, label="语速（倍）")
                volume = gr.Slider(0, 200, value=100, step=1, label="音量（%）")
                tone = gr.Dropdown(choices=[("自然", "neutral"), ("亲切", "warm"), ("活力", "energetic"), ("沉稳", "steady")], value="neutral", label="语调")
                intensity = gr.Slider(0, 1, value=0, step=0.05, label="语调强度")
            applied = gr.JSON(label="当前参数", value=controller.parameters.values())
        gr.Markdown("### 实时话术\n修改当前项会从头重播；已播项禁止修改或删除，请在后续待播条目中修改，或新增话术。选择一行后编辑。")
        items = gr.Dataframe(headers=["编号", "状态", "话术"], datatype=["number", "str", "str"], interactive=False)
        with gr.Row():
            item_id = gr.Number(label="目标话术编号", precision=0, minimum=1)
            edited = gr.Textbox(label="修改 / 新增话术", lines=2)
            after_id = gr.Number(label="新增到此编号之后（0 表示末尾）", value=0, precision=0, minimum=0)
        with gr.Row():
            add = gr.Button("添加")
            edit = gr.Button("修改")
            delete = gr.Button("删除")
        with gr.Accordion("延迟、欠载与编辑响应报告", open=False):
            metrics = gr.JSON(label="实时指标（完成后自动保存 metrics.json 与 playback.wav）")
        start.click(action(controller.start), [text, script_file, voice], message, api_name="start", queue=False)
        stop.click(controller.stop, outputs=message, api_name="stop", queue=False)
        add.click(action(controller.add), [edited, after_id], message, api_name="add", queue=False)
        edit.click(action(controller.edit), [item_id, edited], message, api_name="edit", queue=False)
        delete.click(action(controller.delete), item_id, message, api_name="delete", queue=False)
        for component in [speed, volume, tone, intensity]:
            component.change(action(controller.parameters_changed), [speed, volume, tone, intensity], applied,
                             api_name=False, queue=False)
        # One stable endpoint supports reproducible parameter-control tests.
        apply_button = gr.Button("应用参数")
        apply_button.click(action(controller.parameters_changed), [speed, volume, tone, intensity], applied,
                           api_name="parameters", queue=False)
        def select_row(data, event: gr.SelectData):
            row = data.iloc[event.index[0]]
            try:
                return controller.select(int(row.iloc[0]))
            except (ValueError, StopIteration) as error:
                raise gr.Error(str(error) or "话术编号不存在") from error
        items.select(select_row, items, [item_id, edited], api_name=False, queue=False)
        gr.Timer(0.25).tick(refresh, outputs=[items, status, metrics], api_name="status", queue=False)
        app.load(refresh, outputs=[items, status, metrics], api_name=False, queue=False)
    return app


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=7860)
    parser.add_argument("--repo", type=Path, default=Path("/home/ln/AI/index-tts"))
    parser.add_argument("--output", type=Path, default=Path("outputs/webui"))
    args = parser.parse_args()
    output = args.output.resolve()
    engine = Engine(args.repo)
    controller = Controller(engine, output)
    try:
        create_app(controller).launch(server_name=args.host, server_port=args.port, show_error=True)
    finally:
        controller.stop()
        if controller.session:
            controller.session.worker.join()


if __name__ == "__main__":
    main()
