# =========================
# FILE: skills/video_tools.py
# =========================

from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path

from memory.background_jobs import BackgroundJobManager
from utils.clipboard import get_clipboard_text

_YT_RE = re.compile(r"(https?://)?(www\.)?(youtube\.com|youtu\.be)/", re.I)


def _looks_like_youtube_url(text: str) -> bool:
    return bool(_YT_RE.search(text or ""))


def _run(cmd: list[str]) -> str:
    p = subprocess.run(cmd, capture_output=True, text=True, shell=False)
    out = (p.stdout or "") + "\n" + (p.stderr or "")
    if p.returncode != 0:
        raise RuntimeError(out.strip()[:3000])
    return out


def _download_audio(url: str, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    outtmpl = str(out_dir / "audio.%(ext)s")

    _run([
        "yt-dlp",
        "-x",
        "--audio-format", "wav",
        "--audio-quality", "0",
        "-o", outtmpl,
        url,
    ])

    wavs = list(out_dir.glob("audio*.wav"))
    if not wavs:
        wavs = list(out_dir.glob("*.wav"))
    if not wavs:
        raise RuntimeError("Audio WAV not found after yt-dlp.")
    return wavs[0]


def _transcribe_with_stt(stt, wav_path: Path) -> str:
    if hasattr(stt, "transcribe_file"):
        return (stt.transcribe_file(str(wav_path)) or "").strip()
    raise RuntimeError("Your STT does not support transcribe_file().")


def _summarize(brain, transcript: str, url: str) -> str:
    prompt = (
        "You are Jarvis. Summarize the following YouTube/video transcript clearly.\n"
        "Rules:\n"
        "- Hinglish friendly, simple.\n"
        "- Bullet points for key takeaways.\n"
        "- If transcript is noisy, say 'audio unclear' and still try.\n\n"
        f"URL: {url}\n\n"
        f"TRANSCRIPT:\n{transcript}\n"
    )
    return (brain.chat([{"role": "user", "content": prompt}]) or "").strip()


def start_background_youtube_audio_summary(*, text: str, brain, stt, jobs: BackgroundJobManager) -> str:
    url = ""

    for token in (text or "").split():
        if _looks_like_youtube_url(token):
            url = token.strip()
            break

    if not url:
        clip = get_clipboard_text()
        if _looks_like_youtube_url(clip):
            url = clip

    if not url:
        return "Mujhe YouTube/video link nahi mila. Link copy karo, phir bolo: 'Jarvis, is video ko analyze karo'."

    jobs.start()
    job_id = f"yt_{abs(hash(url))}"
    title = "YouTube audio summary"

    def job_fn() -> str:
        with tempfile.TemporaryDirectory() as td:
            out_dir = Path(td)
            wav = _download_audio(url, out_dir)
            transcript = _transcribe_with_stt(stt, wav)
            if not transcript:
                return "Audio se kuch clear transcript nahi bana. Shayad speech kam thi ya noise zyada tha."
            summary = _summarize(brain, transcript, url)
            return (
                f"🎬 Video: {url}\n\n"
                f"🧾 Transcript (short):\n{transcript[:1200]}{'...' if len(transcript)>1200 else ''}\n\n"
                f"🧠 Summary:\n{summary}\n"
            )

    jobs.submit(job_id=job_id, title=title, fn=job_fn)
    return "Theek hai. Main is video ka **audio-based background analysis** start kar raha hoon. Complete hone par main tumhe bata dunga."


# ✅ MOD: router compatibility wrapper (router was calling summarize_youtube_link)
def summarize_youtube_link(text: str, brain=None, stt=None, jobs: BackgroundJobManager | None = None) -> str:
    if brain is None or stt is None:
        return "YouTube summary ke liye mujhe brain + stt chahiye."
    if jobs is None:
        jobs = BackgroundJobManager()
    return start_background_youtube_audio_summary(text=text, brain=brain, stt=stt, jobs=jobs)

# =========================
# END OF FILE: skills/video_tools.py
# =========================
