import os, re, subprocess, logging, time
import speech_recognition as sr
try:
    import pyaudio
except Exception:
    pyaudio = None

# top-level imports
# hack path to include root
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from SPARC.config.config_io import load_config, save_config
from SPARC.config.settings import (
    DEFAULT_BT_MIC_NAME, MIC_PREFER_NAMES, MIC_EXCLUDE_NAMES,
    SR_ADJUST_DURATION_S, SR_PHRASE_TIME_LIMIT_S, SR_LISTEN_TIMEOUT_S,
    SR_ENERGY_FLOOR, SR_DYNAMIC_ENERGY, VOICE_DEBUG
)

log = logging.getLogger(__name__)

def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.lower()).strip()

def _pactl(cmd: list[str]) -> str:
    try:
        out = subprocess.check_output(["pactl"] + cmd, stderr=subprocess.STDOUT, text=True, timeout=1.5)
        return out.strip()
    except Exception:
        return ""

def list_portaudio_inputs():
    devs = []
    if not pyaudio: return devs
    pa = pyaudio.PyAudio()
    try:
        for i in range(pa.get_device_count()):
            info = pa.get_device_info_by_index(i)
            if int(info.get("maxInputChannels", 0)) > 0:
                devs.append((i, info.get("name", f"dev{i}")))
    finally:
        pa.terminate()
    return devs

def list_sr_mics():
    try:
        names = sr.Microphone.list_microphone_names() or []
        return [(i, n) for i, n in enumerate(names)]
    except Exception:
        return []

def env_overrides():
    idx = os.getenv("SPARC_MIC_INDEX")
    name = os.getenv("SPARC_MIC_NAME")
    return idx, name

def _prefer_score(name: str) -> int:
    n = _norm(name)
    if any(x in n for x in MIC_EXCLUDE_NAMES):
        return -100
    score = 0
    for p in MIC_PREFER_NAMES:
        if p in n:
            score += 10
    if "blue" in n:
        score += 3
    return score

class VoiceListener:
    def __init__(self):
        self.rec = sr.Recognizer()
        self.rec.dynamic_energy_threshold = SR_DYNAMIC_ENERGY
        self.rec.energy_threshold = SR_ENERGY_FLOOR
        self._cached_device = None  # (idx,name) for SR

        # Load persisted config
        self._cfg = load_config()
        self._cfg_audio = self._cfg.get("audio", {})

        if VOICE_DEBUG:
            log.info("=== Audio diagnostics ===")
            log.info("PortAudio inputs:")
            for i, n in list_portaudio_inputs():
                log.info(f"  [PA {i}] {n}")
            log.info("SpeechRecognition mic names:")
            for i, n in list_sr_mics():
                log.info(f"  [SR {i}] {n}")
            log.info(f"Pulse default source: {_pactl(['get-default-source']) or '(unknown)'}")
            log.info(f"Pulse info:\n{_pactl(['info'])}")

    def available(self) -> bool:
        # We will always try to open something at listen time
        return True

    def _candidate_sr_devices(self):
        idx_env, name_env = env_overrides()
        sr_list = list_sr_mics()
        cand = []

        # 0) ENV overrides (highest priority)
        if idx_env is not None:
            try:
                idx = int(idx_env)
                name = next((n for i,n in sr_list if i == idx), f"index:{idx}")
                cand.append((idx, name, 10000))
            except Exception:
                pass
        if name_env:
            nn = _norm(name_env)
            for i,n in sr_list:
                if nn in _norm(n):
                    cand.append((i, n, 9900))

        # 1) Persisted config
        cfg_idx = self._cfg_audio.get("preferred_mic_index")
        cfg_name = self._cfg_audio.get("preferred_mic_name") or ""
        if cfg_idx is not None:
            name = next((n for i,n in sr_list if i == cfg_idx), f"index:{cfg_idx}")
            cand.append((cfg_idx, name, 9500))
        if cfg_name:
            nn = _norm(cfg_name)
            for i,n in sr_list:
                if nn in _norm(n):
                    cand.append((i, n, 9400))

        # 2) Hard default BT mic name from settings (your bluez_input id)
        if DEFAULT_BT_MIC_NAME:
            nn = _norm(DEFAULT_BT_MIC_NAME)
            for i,n in sr_list:
                if nn in _norm(n):
                    cand.append((i, n, 9300))
        else:
            # broader 'bluez_input' fallback
            for i,n in sr_list:
                if "bluez_input" in _norm(n):
                    cand.append((i, n, 9200))

        # 3) Preferred-name ranking
        for i,n in sr_list:
            cand.append((i, n, _prefer_score(n)))

        # Dedup + rank
        best = {}
        for i, n, s in cand:
            if (i not in best) or (s > best[i][1]):
                best[i] = (n, s)
        ranked = sorted([(i, n, s) for i,(n,s) in best.items()], key=lambda x: x[2], reverse=True)
        return [(i, n) for i,n,_ in ranked]

    def _listen_with_device(self, idx: int, name: str, timeout_s, phrase_time_limit_s) -> str:
        try:
            with sr.Microphone(device_index=idx) as source:
                self.rec.adjust_for_ambient_noise(source, duration=SR_ADJUST_DURATION_S)
                audio = self.rec.listen(source, timeout=timeout_s, phrase_time_limit=phrase_time_limit_s)
            try:
                text = self.rec.recognize_google(audio, language="en-IN")
            except Exception:
                text = self.rec.recognize_google(audio, language="en-US")
            return _norm(text)
        except sr.WaitTimeoutError:
            if VOICE_DEBUG: print(f"[VOICE] Timeout on device [{idx}] {name}")
            return ""
        except Exception as e:
            if VOICE_DEBUG: print(f"[VOICE] Error on device [{idx}] {name}: {e}")
            return ""

    def listen_once(self, timeout_s=SR_LISTEN_TIMEOUT_S, phrase_time_limit_s=SR_PHRASE_TIME_LIMIT_S) -> str:
        # cached first
        if self._cached_device:
            idx, name = self._cached_device
            text = self._listen_with_device(idx, name, timeout_s, phrase_time_limit_s)
            if text:
                if VOICE_DEBUG: print(f"[VOICE] Recognized on cached [{idx}] {name}: \"{text}\"")
                # persist (cached already chosen earlier)
                self._persist_choice(idx, name)
                return text
            else:
                if VOICE_DEBUG: print(f"[VOICE] Cached device returned empty; will re-scan.")

        # ranked candidates
        for idx, name in self._candidate_sr_devices():
            text = self._listen_with_device(idx, name, timeout_s, phrase_time_limit_s)
            if text:
                if VOICE_DEBUG: print(f"[VOICE] Recognized on [{idx}] {name}: \"{text}\"")
                self._cached_device = (idx, name)
                self._persist_choice(idx, name)
                return text

        # default fallback
        try:
            with sr.Microphone() as source:
                self.rec.adjust_for_ambient_noise(source, duration=SR_ADJUST_DURATION_S)
                audio = self.rec.listen(source, timeout=timeout_s, phrase_time_limit=phrase_time_limit_s)
            text = self.rec.recognize_google(audio, language="en-IN")
            text = _norm(text)
            if text:
                if VOICE_DEBUG: print(f"[VOICE] Recognized on default: \"{text}\"")
                # cannot persist unknown index; leave as is
                return text
        except Exception:
            pass

        if VOICE_DEBUG: print("[VOICE] No speech recognized on any device.")
        return ""

    def _persist_choice(self, idx: int, name: str) -> None:
        # Save to config so it survives reboot
        self._cfg["audio"]["preferred_mic_index"] = idx
        self._cfg["audio"]["preferred_mic_name"] = name
        save_config(self._cfg)
