# file: d455_center_distance.py
import pyrealsense2 as rs
import numpy as np
import cv2
import time

# 1) Configure streams
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

# 2) Start and create align object (align depth to color)
profile = pipeline.start(config)
align = rs.align(rs.stream.color)

# Helpful if you ever want raw depth units:
depth_sensor = profile.get_device().first_depth_sensor()
depth_scale = depth_sensor.get_depth_scale()  # meters per depth unit

print(f"[i] Depth scale: {depth_scale:.6f} m per unit")

# 3) Main loop
try:
    while True:
        frames = pipeline.wait_for_frames()
        aligned = align.process(frames)
        depth_frame = aligned.get_depth_frame()
        color_frame = aligned.get_color_frame()
        if not depth_frame or not color_frame:
            continue

        # Convert for display
        depth_image = np.asanyarray(depth_frame.get_data())
        color_image = np.asanyarray(color_frame.get_data())
        depth_vis = cv2.applyColorMap(
            cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET
        )

        h, w = depth_image.shape
        cx, cy = w // 2, h // 2

        # (A) Single-pixel distance at image center (meters)
        d_center_m = depth_frame.get_distance(cx, cy)

        # (B) Robust median over a small 5x5 ROI around center (ignores zeros)
        k = 5
        x1, x2 = max(cx - k//2, 0), min(cx + (k+1)//2, w)
        y1, y2 = max(cy - k//2, 0), min(cy + (k+1)//2, h)
        vals = []
        for yy in range(y1, y2):
            for xx in range(x1, x2):
                d = depth_frame.get_distance(xx, yy)
                if d > 0:
                    vals.append(d)
        d_median_m = float(np.median(vals)) if vals else 0.0

        # Overlay text on color preview
        overlay = color_image.copy()
        cv2.circle(overlay, (cx, cy), 4, (0, 255, 255), -1)
        txt = f"Center: {d_center_m:0.3f} m | 5x5 median: {d_median_m:0.3f} m"
        cv2.putText(overlay, txt, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (20, 20, 255), 2)

        # Show color + small depth view
        cv2.imshow("D455 Color (distance overlay)", overlay)
        cv2.imshow("D455 Depth (viz)", depth_vis)

        key = cv2.waitKey(1) & 0xFF
        if key == 27 or key == ord('q'):
            break

finally:
    pipeline.stop()
    cv2.destroyAllWindows()
