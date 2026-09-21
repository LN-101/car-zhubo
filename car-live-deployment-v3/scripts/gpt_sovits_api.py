"""Launch the existing API with tested stream boundaries and reference caching."""
import argparse
import os
from pathlib import Path
import runpy
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--gpt-root', type=Path, required=True)
    args, upstream_args = parser.parse_known_args()
    root = args.gpt_root.resolve()
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
    sys.path.insert(0, str(root))
    sys.path.insert(0, str(root / 'GPT_SoVITS'))
    os.chdir(root)
    sys.argv = [str(root / 'api_v2.py'), *upstream_args]
    import torch
    torch.set_num_threads(4)
    from app.gpt_sovits_runtime import install
    install()
    api = runpy.run_path(str(root / 'api_v2.py'), run_name='car_live_gpt_api')
    pipeline = api['tts_pipeline']

    @api['APP'].get('/runtime/status')
    def runtime_status():
        return {
            'runtime': 'car-live-gpt-sovits', 'revision': 1,
            'gpt_weights': str(Path(pipeline.configs.t2s_weights_path).resolve()),
            'sovits_weights': str(Path(pipeline.configs.vits_weights_path).resolve()),
            'reference_cache_size': len(getattr(pipeline, '_voice_cache', {})),
            'reference_cache_hits': getattr(pipeline, '_voice_cache_hits', 0),
            'device': str(pipeline.configs.device),
        }

    @api['APP'].post('/runtime/prime')
    def prime_reference(request: dict):
        for _ in pipeline.run({**request, '_prepare_reference_only': True}):
            pass
        return {'ready': True}

    api['uvicorn'].run(api['APP'], host=api['host'], port=api['port'], workers=1)


if __name__ == '__main__':
    main()
