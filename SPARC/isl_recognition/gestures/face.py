"""
Head gesture detection (Head Nod, Head Rotate).
"""
from collections import deque

def detect_head_gesture(results, head_history):
    """
    Detect head gestures: nod (up/down) = Yes, rotate (left/right) = No
    Returns: (gesture_name, confidence) or (None, 0.0)
    """
    if not results.face_landmarks:
        return None, 0.0
    
    face_landmarks = results.face_landmarks.landmark
    
    # Use nose tip (landmark 4) and forehead (landmark 10) for head position
    nose_tip = face_landmarks[4]
    forehead = face_landmarks[10]
    
    # Calculate head center position
    head_center_x = (nose_tip.x + forehead.x) / 2
    head_center_y = (nose_tip.y + forehead.y) / 2
    
    # Add to history
    head_history.append((head_center_x, head_center_y))
    
    # Need at least 5 frames to detect movement
    if len(head_history) < 5:
        return None, 0.0
    
    # Calculate movement patterns
    recent_positions = list(head_history)
    
    # Vertical movement (for nod)
    y_positions = [pos[1] for pos in recent_positions]
    y_range = max(y_positions) - min(y_positions)
    
    # Horizontal movement (for rotate)
    x_positions = [pos[0] for pos in recent_positions]
    x_range = max(x_positions) - min(x_positions)
    
    # Thresholds
    # Optimization: Tuned slightly for better response
    nod_threshold = 0.03
    rotate_threshold = 0.04
    
    # Detect head nod (Yes)
    if y_range > nod_threshold and y_range > x_range * 1.5:
        y_mean = sum(y_positions) / len(y_positions)
        y_variance = sum((y - y_mean) ** 2 for y in y_positions) / len(y_positions)
        if y_variance > 0.0001:
            confidence = min(90.0, (y_range / nod_threshold) * 30)
            return "head_nod", confidence
    
    # Detect head rotate (No)
    if x_range > rotate_threshold and x_range > y_range * 1.5:
        x_mean = sum(x_positions) / len(x_positions)
        x_variance = sum((x - x_mean) ** 2 for x in x_positions) / len(x_positions)
        if x_variance > 0.0001:
            confidence = min(90.0, (x_range / rotate_threshold) * 30)
            return "head_rotate", confidence
    
    return None, 0.0
