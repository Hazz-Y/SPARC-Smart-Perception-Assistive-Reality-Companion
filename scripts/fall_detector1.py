#!/usr/bin/env python3
import os, time, math, subprocess
import numpy as np
import requests
import pyrealsense2 as rs

# ---- Tunables ----
G = 9.80665
FREEFALL_G_MAX  = float(os.environ.get("FREEFALL_G_MAX", 0.35 * G))
IMPACT_G_MIN    = float(os.environ.get("IMPACT_G_MIN",   2.5  * G))
ORIENT_DEG_MIN  = float(os.environ.get("ORIENT_DEG_MIN", 45.0))
WINDOW_S        = float(os.environ.get("WINDOW_S", 1.5))
COOLDOWN_S      = float(os.environ.get("COOLDOWN_S", 8.0))
ALPHA           = float(os.environ.get("LPF_ALPHA", 0.20))

PHONE_PORT      = int(os.environ.get("PHONE_PORT", "5050"))
AUTH_TOKEN      = os.environ.get("FALL_TOKEN", "")

FRAME_TIMEOUT_MS = int(os.environ.get("FRAME_TIMEOUT_MS", "10000"))  # was 5000
MAX_CONSEC_TIMEOUTS = int(os.environ.get("MAX_CONSEC_TIMEOUTS", "3"))
RESTART_BACKOFF_S = float(os.environ.get("RESTART_BACKOFF_S", "1.0"))

def header(): return {"X-Auth": AUTH_TOKEN} if AUTH_TOKEN else {}

def detect_gw_ip():
    out = subprocess.check_output(["ip","route"], text=True)
    for line in out.splitlines():
        if line.startswith("default "):
            return line.split()[2]
    return None

def get_phone_base_url():
    ip = os.environ.get("PHONE_IP") or detect_gw_ip() or "192.168.43.1"
    return f"http://{ip}:{PHONE_PORT}"

def magnitude(v): return float(np.linalg.norm(v))

def vec_angle_deg(a,b):
    na, nb = magnitude(a), magnitude(b)
    if na<1e-8 or nb<1e-8: return 0.0
    c = max(-1.0, min(1.0, float(np.dot(a,b)/(na*nb))))
    return math.degrees(math.acos(c))

# ---- Phone interactions (force reliable indoor provider) ----
def request_phone_location(base_url, timeout=8):
    url = f"{base_url}/location?provider=network&timeout=12"
    r = requests.get(url, headers=header(), timeout=timeout+6)
    j = r.json()
    if not j.get("ok"):
        raise RuntimeError(j.get("error"))
    loc = j["location"]
    return float(loc["lat"]), float(loc["lon"]), loc.get("accuracy_m")

def open_maps_on_phone(base_url, lat, lon, timeout=8):
    payload = {"lat": lat, "lon": lon, "label": "Fall detected"}
    r = requests.post(f"{base_url}/open_map", json=payload, headers=header(), timeout=timeout)
    jr = r.json()
    if not jr.get("ok"):
        raise RuntimeError(jr.get("error"))
    print(f"[ALERT] Asked phone to open Maps at {lat:.6f},{lon:.6f}")

# ---- IMU pipeline helpers ----
def start_pipeline_relaxed():
    pipe = rs.pipeline(); cfg = rs.config()
    try:
        cfg.enable_stream(rs.stream.accel, rs.format.motion_xyz32f)
        cfg.enable_stream(rs.stream.gyro,  rs.format.motion_xyz32f)
        prof = pipe.start(cfg)
        print("[i] IMU started with SDK-chosen profiles.")
        return pipe, prof
    except Exception as e1:
        print("[w] Default IMU start failed:", e1)

    pipe2 = rs.pipeline(); cfg2 = rs.config()
    wrp = rs.pipeline_wrapper(pipe2); sel = cfg2.resolve(wrp); dev = sel.get_device()
    print("[i] Device:", dev.get_info(rs.camera_info.name))

    accel_fps, gyro_fps = None, None
    for s in dev.sensors:
        for p in s.get_stream_profiles():
            if p.stream_type() == rs.stream.accel and p.format()==rs.format.motion_xyz32f:
                accel_fps = max(accel_fps or 0, p.fps())
            if p.stream_type() == rs.stream.gyro  and p.format()==rs.format.motion_xyz32f:
                gyro_fps  = max(gyro_fps  or 0, p.fps())
    if accel_fps is None: accel_fps = 63
    if gyro_fps  is None: gyro_fps  = 200
    print(f"[i] Trying IMU fps accel={accel_fps}Hz gyro={gyro_fps}Hz")

    cfg2.enable_stream(rs.stream.accel, rs.format.motion_xyz32f, accel_fps)
    cfg2.enable_stream(rs.stream.gyro,  rs.format.motion_xyz32f, gyro_fps)
    prof2 = pipe2.start(cfg2)
    print("[i] IMU started with enumerated profiles.")
    return pipe2, prof2

def restart_pipeline():
    # small backoff to let USB settle
    time.sleep(RESTART_BACKOFF_S)
    return start_pipeline_relaxed()

def main():
    base = get_phone_base_url()
    print(f"[i] Phone base URL: {base}")
    if AUTH_TOKEN: print("[i] Using X-Auth token")

    try:
        pipeline, profile = start_pipeline_relaxed()
    except Exception as e:
        print("[!] Could not start IMU streams:", e)
        print("    Check USB3/cable and verify IMU in realsense-viewer.")
        return

    print("[i] IMU running. Press Ctrl+C to stop.")
    last_a = np.array([0.0,0.0,G], dtype=float)

    state = "IDLE"
    t_freefall = 0.0
    last_alert = 0.0
    orientation_ref = np.array([0.0,0.0,1.0], dtype=float)
    impact_peak = 0.0

    consec_timeouts = 0

    try:
        while True:
            try:
                # NOTE: Python binding supports timeout in ms
                frames = pipeline.wait_for_frames(FRAME_TIMEOUT_MS)
                consec_timeouts = 0  # got a frame → reset counter
            except Exception as e:
                consec_timeouts += 1
                print(f"[w] IMU timeout ({consec_timeouts}/{MAX_CONSEC_TIMEOUTS}): {e}")
                if consec_timeouts >= MAX_CONSEC_TIMEOUTS:
                    print("[i] Restarting IMU pipeline…")
                    try:
                        pipeline.stop()
                    except Exception:
                        pass
                    pipeline, profile = restart_pipeline()
                    consec_timeouts = 0
                continue

            accel = frames.first_or_default(rs.stream.accel)
            if not accel:
                time.sleep(0.002); continue

            d = accel.as_motion_frame().get_motion_data()
            a = np.array([d.x, d.y, d.z], dtype=float)

            # low-pass filter
            last_a = ALPHA*a + (1-ALPHA)*last_a
            a_mag = magnitude(last_a)
            now = time.time()

            if state=="IDLE":
                if a_mag < FREEFALL_G_MAX:
                    state = "FREEFALL"; t_freefall = now; impact_peak = 0.0
                    if magnitude(last_a) > 1e-6:
                        orientation_ref = last_a / magnitude(last_a)

            elif state=="FREEFALL":
                if now - t_freefall > WINDOW_S:
                    state = "IDLE"
                if a_mag > IMPACT_G_MIN:
                    impact_peak = a_mag; state = "IMPACT"

            elif state=="IMPACT":
                if now - t_freefall > WINDOW_S:
                    state = "IDLE"
                else:
                    if magnitude(last_a)>1e-6 and magnitude(orientation_ref)>1e-6:
                        cur = last_a / magnitude(last_a)
                        delta = vec_angle_deg(orientation_ref, cur)
                        if delta >= ORIENT_DEG_MIN:
                            if now - last_alert >= COOLDOWN_S:
                                print(f"[ALERT] impact={impact_peak/G:.2f}g Δorient={delta:.1f}°")
                                try:
                                    lat, lon, acc = request_phone_location(base)
                                    print(f"[i] Phone (network) GPS: {lat:.6f},{lon:.6f} (±{acc} m)")
                                    open_maps_on_phone(base, lat, lon)
                                    last_alert = now
                                except Exception as e:
                                    print("[ERR] phone call failed:", e)
                            state = "IDLE"

            time.sleep(0.002)

    except KeyboardInterrupt:
        pass
    finally:
        try:
            pipeline.stop()
        except Exception:
            pass
        print("\n[i] Stopped.")

if __name__ == "__main__":
    main()
