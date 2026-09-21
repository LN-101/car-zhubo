"""Offline Chinese ASR audit using an already installed SenseVoice checkpoint."""
import argparse
import json
from pathlib import Path
import re


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('results', type=Path)
    parser.add_argument('--model', type=Path, default=Path.home() / '.cache/modelscope/models/iic--SenseVoiceSmall/snapshots/master')
    args = parser.parse_args()
    if not (args.model / 'model.pt').is_file():
        raise SystemExit('Local SenseVoice checkpoint is missing')
    from funasr import AutoModel
    model = AutoModel(model=str(args.model), device='cpu', ncpu=2, disable_update=True, disable_pbar=True)
    records = json.loads(args.results.read_text(encoding='utf-8'))
    for record in records:
        if not record.get('ok'):
            continue
        result = model.generate(input=record['audio'], language='zh', use_itn=False, disable_pbar=True)
        record['asr_text'] = re.sub(r'<\|.*?\|>', '', result[0]['text']).strip()
        print(json.dumps({'voice': record['voice'], 'text': record['text'], 'asr': record['asr_text']}, ensure_ascii=True), flush=True)
    args.results.with_name('asr.json').write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
