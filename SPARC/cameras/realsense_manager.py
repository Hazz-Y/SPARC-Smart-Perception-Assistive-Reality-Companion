"""
RealSense/USB Camera Manager for SPARC
Handles RealSense D455 or USB fallback. Keeps one capture source alive.
"""
import logging
from typing import Optional, Tuple
import numpy as np
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'librealsense'))

try:
    import pyrealsense2 as rs
    REALSENSE_AVAILABLE = True
except ImportError:
    REALSENSE_AVAILABLE = False

import cv2
from SPARC.config.settings import (
    FRAME_WIDTH, FRAME_HEIGHT, FRAME_FPS, ENABLE_DEPTH, DEPTH_ALIGN_TO_COLOR, DEPTH_SAMPLE_BOX,
    DEPTH_CLIP_MIN_M, DEPTH_CLIP_MAX_M, DEPTH_COLOR_MAP, DEPTH_NORM_MODE, DEPTH_NORM_FIXED_MAX_M
)

class RealSenseManager:
    def __init__(self):
        self.logger = logging.getLogger('RealSenseManager')
        self.cap = None
        self.pipeline = None
        self.profile = None
        self.using_realsense = False
        self.align = None
        self.depth_scale = None
        self.depth_sensor = None
        self.colormap_map = {
            "JET": cv2.COLORMAP_JET,
            "TURBO": cv2.COLORMAP_TURBO,
            "INFERNO": cv2.COLORMAP_INFERNO,
            "MAGMA": cv2.COLORMAP_MAGMA,
        }
        if self._try_init_realsense():
            self.using_realsense = True
        else:
            self._init_usb_fallback()

    def _try_init_realsense(self):
        try:
            import pyrealsense2 as rs
            self.rs = rs
            self.pipeline = rs.pipeline()
            cfg = rs.config()
            cfg.enable_stream(rs.stream.color, FRAME_WIDTH, FRAME_HEIGHT, rs.format.bgr8, FRAME_FPS)
            if ENABLE_DEPTH:
                cfg.enable_stream(rs.stream.depth, FRAME_WIDTH, FRAME_HEIGHT, rs.format.z16, FRAME_FPS)
            self.profile = self.pipeline.start(cfg)
            if ENABLE_DEPTH:
                self.depth_sensor = self.profile.get_device().first_depth_sensor()
                self.depth_scale = self.depth_sensor.get_depth_scale()
                if DEPTH_ALIGN_TO_COLOR:
                    self.align = rs.align(rs.stream.color)
            return True
        except Exception as e:
            self.logger.warning(f'RealSense init failed: {e}')
            return False

    def _init_usb_fallback(self):
        for idx in [0, 1, 2, 10, 11, 12]:
            cap = cv2.VideoCapture(idx)
            if cap.isOpened():
                self.cap = cap
                self.logger.info(f'USB camera opened at index {idx}.')
                break
        if self.cap is None:
            self.logger.error('No camera available.')

    def available(self) -> bool:
        return self.using_realsense or (self.cap is not None and self.cap.isOpened())

    def has_depth(self) -> bool:
        return self.using_realsense and (self.depth_scale is not None)

    def get_frames(self):
        if self.using_realsense:
            try:
                frames = self.pipeline.wait_for_frames()
                if self.align:
                    frames = self.align.process(frames)
                color = frames.get_color_frame()
                depth = frames.get_depth_frame() if ENABLE_DEPTH else None
                color_np = np.asanyarray(color.get_data()) if color else None
                depth_np = np.asanyarray(depth.get_data()) if depth else None
                return True, color_np, depth_np
            except Exception as e:
                self.logger.warning(f'RealSense frame error: {e}')
                return False, None, None
        elif self.cap:
            ret, frame = self.cap.read()
            return ret, frame, None
        else:
            return False, None, None

    def get_frame(self):
        ok, color_np, _ = self.get_frames()
        return ok, color_np

    def colorize_depth(self, depth_np):
        if depth_np is None or self.depth_scale is None:
            return None
        # Convert to meters
        depth_m = depth_np.astype(np.float32) * float(self.depth_scale)
        mask = (depth_m > 0)
        # Normalization
        if DEPTH_NORM_MODE == "auto":
            valid = depth_m[mask]
            vmin = DEPTH_CLIP_MIN_M
            vmax = DEPTH_CLIP_MAX_M
            if valid.size > 0:
                vmin = max(vmin, float(np.percentile(valid, 2)))
                vmax = min(vmax, float(np.percentile(valid, 98)))
            norm = np.clip((depth_m - vmin) / (vmax - vmin), 0, 1)
        else:  # fixed
            vmin = 0.0
            vmax = DEPTH_NORM_FIXED_MAX_M
            norm = np.clip((depth_m - vmin) / (vmax - vmin), 0, 1)
        depth_8u = (norm * 255).astype(np.uint8)
        cmap = self.colormap_map.get(DEPTH_COLOR_MAP.upper(), cv2.COLORMAP_JET)
        depth_color = cv2.applyColorMap(depth_8u, cmap)
        return depth_color

    def estimate_distance_bbox(self, x1: int, y1: int, x2: int, y2: int):
        if not self.has_depth():
            return None
        ok, color_np, depth_np = self.get_frames()
        if not ok or depth_np is None:
            return None
        h, w = depth_np.shape[:2]
        cx = int(np.clip((x1 + x2) // 2, 0, w-1))
        cy = int(np.clip((y1 + y2) // 2, 0, h-1))
        k = max(3, int(DEPTH_SAMPLE_BOX) // 2 * 2 + 1)
        x0 = max(0, cx - k//2); x1b = min(w, cx + k//2 + 1)
        y0 = max(0, cy - k//2); y1b = min(h, cy + k//2 + 1)
        roi = depth_np[y0:y1b, x0:x1b]
        valid = roi[(roi > 0)]
        if valid.size == 0 or self.depth_scale is None:
            return None
        d_m = float(np.median(valid)) * float(self.depth_scale)
        d_m = np.clip(d_m, DEPTH_CLIP_MIN_M, DEPTH_CLIP_MAX_M)
        return d_m

    def stop(self) -> None:
        if self.using_realsense and self.pipeline:
            self.pipeline.stop()
            self.logger.info('RealSense pipeline stopped.')
        if self.cap:
            self.cap.release()
            self.logger.info('USB camera released.')

