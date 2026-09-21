"""Exercise actual Gradio event endpoints against a running GPU WebUI.

Run: python tools/validate_live_webui.py --url http://127.0.0.1:7861
"""
import argparse
import json
from pathlib import Path
from time import monotonic, sleep

from gradio_client import Client, handle_file


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:7861")
    parser.add_argument("--output", type=Path, default=Path("outputs/live-edit-validation"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    client = Client(args.url, verbose=False)

    def status():
        result = client.predict(api_name="/status")[2]
        if result.get("error"):
            raise RuntimeError(result["error"])
        return result

    def wait(predicate, timeout=120):
        deadline = monotonic() + timeout
        while monotonic() < deadline:
            data = status()
            if predicate(data):
                return data
            sleep(0.1)
        raise TimeoutError(json.dumps(data, ensure_ascii=False))

    def save(name, data):
        (args.output / name).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    try:
        client.predict("", None, None, api_name="/start")
    except Exception as error:
        assert "非空" in str(error), str(error)
    else:
        raise AssertionError("empty script was accepted")
    text = ("欢迎来到直播间。今天我们介绍欧拉五纯电版。"
            "这款车型适合城市通勤。接下来看看车辆空间。座舱设计方便日常使用。"
            "周末出行也能轻松安排。现在介绍车辆的续航表现。实际续航与路况有关。"
            "接着看看辅助驾驶配置。驾驶时请保持注意力。欢迎继续了解更多细节。"
            "下面看看车内储物空间。日常物品可以方便收纳。接下来介绍后排乘坐体验。"
            "具体配置请以实际车辆为准。欢迎在直播间交流用车需求。感谢大家持续关注。")
    client.predict(text, None, None, api_name="/start")
    data = wait(lambda d: d.get("first_device_output_s") is not None)
    assert data["first_output_within_3s"], data["first_device_output_s"]
    current = data["now_playing"]
    client.predict(current, "欢迎来到直播间。这里是修订后的开场。", api_name="/edit")
    wait(lambda d: any(e["kind"] == "current" and e["first_output_s"] is not None for e in d["edits"]))
    data = status()
    last = data["items"][-1]["id"]
    client.predict(last, "感谢观看，本条话术已经更新。", api_name="/edit")
    client.predict("这是直播中新增的话术。", 0, api_name="/add")
    added = status()["items"][-1]["id"]
    client.predict("这条新增话术将在播放前删除。", 0, api_name="/add")
    data = status()
    inserted = data["items"][-1]["id"]
    client.predict(inserted, api_name="/delete")
    client.predict(1.25, 50, "warm", 0.6, api_name="/parameters")
    data = wait(lambda d: any(i["id"] == current and i["status"] == "已播放" for i in d["items"]))
    client.predict(current, "更正一下，欢迎了解车型信息。", api_name="/edit")
    wait(lambda d: any(e["kind"] == "correction" and e["resume_s"] is not None for e in d["edits"]))
    data = status()
    client.predict(data["now_playing"], api_name="/delete")
    client.predict(0.8, 150, "energetic", 0.5, api_name="/parameters")
    wait(lambda d: any(g["parameters"]["tone"] == "energetic" and not g["discarded"] for g in d["generations"]))
    client.predict(1, 100, "steady", 0.7, api_name="/parameters")
    data = wait(lambda d: d["state"] == "finished", timeout=180)
    assert data["streamed_before_synthesis_done"]
    assert any(p["item_id"] == added for p in data["playback"])
    assert not any(p["item_id"] == inserted for p in data["playback"])
    assert any(e["kind"] == "queued" and e["regeneration_s"] is not None for e in data["edits"])
    assert {"neutral", "warm", "energetic", "steady"}.issubset(
        {g["parameters"]["tone"] for g in data["generations"] if not g["discarded"]})
    save("webui-edit-evidence.json", data)
    # Completed scripts may be edited, but must not restart audio.
    client.predict(current, "结束后只更新文本。", api_name="/edit")
    assert status()["state"] == "finished"
    client.predict(1, 100, "neutral", 0, api_name="/parameters")
    source = args.output / "uploaded-script.txt"
    source.write_text(text, encoding="utf-8")
    client.predict("", handle_file(str(source.resolve())), None, api_name="/start")
    data = wait(lambda d: d.get("first_device_output_s") is not None)
    assert data["first_output_within_3s"], data["first_device_output_s"]
    client.predict(api_name="/stop")
    data = wait(lambda d: d["state"] == "stopped")
    save("webui-file-evidence.json", data)
    print("PASS: text/file input, live edits, exact-resume timestamps, parameters, finish and stop")


if __name__ == "__main__":
    main()
