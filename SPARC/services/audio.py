"""
Audio Service for SPARC
Provides TTS and ping (bell) with graceful fallback.
"""
import os, random, string, logging, time, math, subprocess, shutil
from gtts import gTTS
from SPARC.config.settings import TTS_LANG, AUDIO_TMP

logger = logging.getLogger(__name__)

def _estimate_speech_seconds(text: str) -> float:
    """
    Roughly estimate how long the TTS will take to speak.
    Conservative: assume ~13 chars/sec (≈160 wpm) and add a small fixed pad.
    """
    chars_per_sec = 13.0
    pad = 0.25  # seconds of safety (pulse/alsa buffer drain)
    return max(0.6, len(text) / chars_per_sec) + pad

class AudioService:
    def __init__(self):
        os.makedirs(AUDIO_TMP, exist_ok=True)
        # check mpg123 presence once
        self._mpg123 = shutil.which("mpg123")
        if not self._mpg123:
            logger.warning("mpg123 not found; announcements may fail. Install with: sudo apt-get install mpg123")

    def ping(self):
        try:
            os.system('printf "\a"')
        except Exception:
            pass

    def say(self, text: str):
        """
        Synchronous, blocking TTS playback.
        - Generate MP3 with gTTS.
        - Play via mpg123 using subprocess.run (blocks until finished).
        - Add a short safety sleep to avoid truncation on some sinks.
        """
        if not text:
            return
        try:
            fname = ''.join(random.choice(string.ascii_lowercase) for _ in range(8)) + ".mp3"
            path = os.path.join(AUDIO_TMP, fname)
            gTTS(text=text, lang=TTS_LANG).save(path)

            if self._mpg123:
                # -q = quiet; block until completion
                try:
                    subprocess.run([self._mpg123, "-q", path], check=False)
                except Exception as e:
                    logger.warning(f"mpg123 playback failed: {e}")
            else:
                # Fallback: try aplay (wav only) or skip (we have mp3)
                logger.warning("No mpg123 available; cannot play MP3 synchronously.")

            # Small safety wait to ensure buffer fully drains
            time.sleep(_estimate_speech_seconds(text) * 0.10)  # 10% of estimated time, min inside estimator pad

        except Exception as e:
            logger.warning(f"TTS failed: {e}")
        finally:
            try:
                if 'path' in locals() and os.path.exists(path):
                    os.remove(path)
            except Exception:
                pass

    def say_random(self, lines: list[str]):
        if not lines:
            return
        self.say(random.choice(lines))

