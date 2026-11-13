from functools import lru_cache
from pathlib import Path

import soundfile as sf
import torch
from demucs.apply import apply_model
from demucs.audio import AudioFile
from demucs.pretrained import get_model
import os

from app.config import OUTPUT_DIR

torch.set_num_threads(max(1, (os.cpu_count() or 2) // 2))

MODEL_NAME = "htdemucs"


class SeparationError(Exception):
    pass


@lru_cache(maxsize=1)
def load_model():
    model = get_model(MODEL_NAME)
    model.eval()
    return model


def save_wav(path: Path, audio: torch.Tensor, samplerate: int) -> None:
    data = audio.clamp(-1, 1).T.numpy()  # soundfile wants (time, channels)
    sf.write(str(path), data, samplerate)


def separate(input_path: Path) -> Path:
    """Split a song into vocals.wav and no_vocals.wav. Returns the output folder."""
    try:
        model = load_model()
        wav = AudioFile(input_path).read(
            streams=0, # type: ignore
            samplerate=model.samplerate,
            channels=model.audio_channels,
        )
        ref = wav.mean(0)
        wav = (wav - ref.mean()) / ref.std()

        with torch.no_grad():
            sources = apply_model(
                model, wav[None], device="cpu",
                split=True, overlap=0.25, num_workers=1, progress=True,
            )[0]
        sources = sources * ref.std() + ref.mean()

        vocals_index = model.sources.index("vocals")
        vocals = sources[vocals_index]
        no_vocals = sum(s for i, s in enumerate(sources) if i != vocals_index)

        out_dir = OUTPUT_DIR / input_path.stem
        out_dir.mkdir(parents=True, exist_ok=True)
        save_wav(out_dir / "vocals.wav", vocals, model.samplerate)
        save_wav(out_dir / "no_vocals.wav", no_vocals, model.samplerate) # type: ignore
        return out_dir
    except Exception as e:
        raise SeparationError(str(e)) from e