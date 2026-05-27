"""
Object Detection for SPARC
Runs YOLOv8 on camera frames, returns unique detected class names.
"""
import logging
from typing import List
import cv2
from SPARC.config import settings

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False

def _fmt_dist(m):
    if m is None: return ""
    if m < 1.0:   return f"{int(m*100)} cm"
    return f"{m:.1f} m"

def _summarize(objs):
    if not objs:
        return "I don't see any objects right now.", "None"
    names = [o["name"] + (f" ({_fmt_dist(o['distance_m'])})" if o.get("distance_m") else "") for o in objs]
    if len(names) == 1:
        return f"I can see a {names[0]}", names[0][:18]
    if len(names) == 2:
        return f"I can see a {names[0]} and a {names[1]}", (names[0][:9] + ", " + names[1][:8])
    last = names[-1]
    first = ", ".join(names[:-1])
    return f"I can see {first}, and a {last}", (names[0][:9] + ", " + names[1][:9])

class ObjectDetector:
    def __init__(self):
        self.logger = logging.getLogger('ObjectDetector')
        if YOLO_AVAILABLE:
            try:
                self.model = YOLO(str(settings.YOLO_WEIGHTS))
            except Exception as e:
                self.logger.error(f'YOLO model load failed: {e}')
                self.model = None
        else:
            self.logger.error('ultralytics not available.')
            self.model = None

    def run_once(self, camera, window_rgb="SPARC RGB", window_depth="SPARC Depth", duration_s=None):
        from SPARC.config.settings import OBJECT_DET_DURATION_S
        import time
        import numpy as np
        import cv2
        if duration_s is None:
            duration_s = OBJECT_DET_DURATION_S
        if not camera or not camera.available():
            self.logger.error('No camera available for object detection.')
            return [], "I don't see any objects right now.", "None"
        if not self.model:
            self.logger.error('YOLO model unavailable.')
            return [], "I don't see any objects right now.", "None"
        has_depth = hasattr(camera, 'has_depth') and camera.has_depth()
        if has_depth:
            cv2.namedWindow(window_rgb)
            cv2.namedWindow(window_depth)
        else:
            cv2.namedWindow(window_rgb)
        start = time.time()
        results_all = []
        shown_depth = False
        while time.time() - start < duration_s:
            ok, color_np, depth_np = camera.get_frames()
            if not ok or color_np is None:
                continue
            frame = color_np.copy()
            depth_color = None
            if has_depth and depth_np is not None:
                depth_color = camera.colorize_depth(depth_np)
            results = self.model(frame, verbose=False)
            for r in results:
                boxes = r.boxes
                for box in boxes:
                    cls = int(box.cls[0])
                    name = self.model.names[cls]
                    xyxy = box.xyxy[0].cpu().numpy().astype(int)
                    conf = float(box.conf[0])
                    dist = None
                    if has_depth and depth_np is not None:
                        dist = camera.estimate_distance_bbox(int(xyxy[0]), int(xyxy[1]), int(xyxy[2]), int(xyxy[3]))
                    results_all.append({"name": name, "distance_m": dist})
                    label = f"{name}:{conf:.2f} {_fmt_dist(dist)}"
                    cv2.rectangle(frame, tuple(xyxy[:2]), tuple(xyxy[2:]), (0,255,0), 2)
                    cv2.putText(frame, label, tuple(xyxy[:2]), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)
                    if has_depth and depth_color is not None:
                        # Overlay on depth window at bbox center
                        cx = int((xyxy[0] + xyxy[2]) // 2)
                        cy = int((xyxy[1] + xyxy[3]) // 2)
                        cv2.putText(depth_color, _fmt_dist(dist), (cx, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2)
            cv2.imshow(window_rgb, frame)
            if has_depth and depth_color is not None:
                cv2.imshow(window_depth, depth_color)
                shown_depth = True
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        if has_depth:
            cv2.destroyWindow(window_rgb)
            if shown_depth:
                cv2.destroyWindow(window_depth)
        else:
            cv2.destroyWindow(window_rgb)
        # dedupe by (name, rounded distance)
        seen = set(); unique = []
        for o in results_all:
            key = (o["name"], None if o["distance_m"] is None else round(o["distance_m"], 1))
            if key in seen: continue
            seen.add(key); unique.append(o)
        speech, oled_line = _summarize(unique)
        return unique, speech, oled_line

