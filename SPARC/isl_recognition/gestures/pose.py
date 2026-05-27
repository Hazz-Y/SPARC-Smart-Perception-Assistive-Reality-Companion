"""
Pose and body-based gesture detection.
"""
import numpy as np
from ..utils import distance, calculate_angle, get_shoulder_width

def detect_namaste_gesture(results):
    """
    Detect 'Namaste' / 'Prayer Hands'.
    """
    if not results.pose_landmarks:
        return False, 0.0
    if not results.left_hand_landmarks or not results.right_hand_landmarks:
        return False, 0.0
    
    # Landmarks
    pose = results.pose_landmarks.landmark
    left_hand = results.left_hand_landmarks.landmark
    right_hand = results.right_hand_landmarks.landmark
    
    # Calculate shoulder width for normalization
    shoulder_width = get_shoulder_width(pose)
    if shoulder_width < 0.05:
        return False, 0.0
        
    # Wrist Distance Rule
    wrist_distance = distance(left_hand[0], right_hand[0])
    wrist_threshold = 0.20 * shoulder_width
    if wrist_distance >= wrist_threshold:
        return False, 0.0 # Optimization: Fail fast
        
    # Palm Center Proximity Rule
    palm_distance = distance(left_hand[5], right_hand[5])
    palm_threshold = 0.18 * shoulder_width
    if palm_distance >= palm_threshold:
        return False, 0.0
        
    # Hands Upright Rule
    if left_hand[8].y >= left_hand[0].y or right_hand[8].y >= right_hand[0].y:
        return False, 0.0
        
    # Check Symmetry
    y_diff = abs(left_hand[8].y - right_hand[8].y)
    x_diff = abs(left_hand[8].x - right_hand[8].x)
    
    if y_diff < 0.10 * shoulder_width and x_diff < 0.12 * shoulder_width:
        # Calculate confidence
        conf_scores = [
            1.0 - (wrist_distance / wrist_threshold),
            1.0 - (palm_distance / palm_threshold),
            1.0 - (y_diff / (0.10 * shoulder_width))
        ]
        avg_conf = sum(conf_scores) / len(conf_scores) * 100
        return True, min(95.0, avg_conf)
        
    return False, 0.0

def detect_hands_intersection(results):
    """Detect 'Home' gesture (hands intersection)."""
    if not results.left_hand_landmarks or not results.right_hand_landmarks:
        return False, 0.0
        
    left_hand = results.left_hand_landmarks.landmark
    right_hand = results.right_hand_landmarks.landmark
    
    # Find topmost points (min y)
    try:
        left_top = min(left_hand, key=lambda lm: lm.y)
        right_top = min(right_hand, key=lambda lm: lm.y)
    except ValueError:
        return False, 0.0
        
    dist = distance(left_top, right_top)
    intersection_threshold = 0.08
    
    if dist < intersection_threshold:
        confidence = min(95.0, 70.0 + (25.0 * (1.0 - dist / intersection_threshold)))
        return True, confidence
        
    return False, 0.0

def detect_india_gesture(results):
    """Detect 'I am Indian' gesture."""
    if not results.left_hand_landmarks or not results.pose_landmarks or not results.face_landmarks:
        return False, 0.0
        
    left_hand = results.left_hand_landmarks.landmark
    pose = results.pose_landmarks.landmark
    face = results.face_landmarks.landmark
    
    # Baselines
    shoulder_baseline_y = (pose[11].y + pose[12].y) / 2
    eyebrow_baseline_y = (face[66].y + face[296].y) / 2 # Approx middle of eyebrows
    
    # Thumb condition
    thumb_tip = left_hand[4]
    if thumb_tip.y >= eyebrow_baseline_y:
        return False, 0.0
        
    # Hand above shoulder condition
    try:
        hand_top_y = min(lm.y for lm in left_hand)
    except ValueError:
        return False, 0.0
        
    if hand_top_y >= shoulder_baseline_y:
        return False, 0.0
        
    # Calculate confidence
    dist_eyebrow = eyebrow_baseline_y - thumb_tip.y
    dist_shoulder = shoulder_baseline_y - hand_top_y
    
    conf = 70.0 + (min(1.0, dist_eyebrow / 0.05) * 15.0) + (min(1.0, dist_shoulder / 0.1) * 15.0)
    return True, min(95.0, conf)

def detect_sibling_gesture(results):
    """Detect 'Sibling' gesture."""
    if not results.pose_landmarks:
        return False, 0.0
        
    pose = results.pose_landmarks.landmark
    touch_threshold = 0.04
    
    # Check Right Hand -> Right Shoulder
    if results.right_hand_landmarks:
        middle_tip = results.right_hand_landmarks.landmark[12]
        shoulder = pose[12] # Right shoulder
        dist = distance(middle_tip, shoulder)
        if dist < touch_threshold:
             return True, min(95.0, 75.0 + (20.0 * (1.0 - dist / touch_threshold)))
             
    # Check Left Hand -> Left Shoulder
    if results.left_hand_landmarks:
        middle_tip = results.left_hand_landmarks.landmark[12]
        shoulder = pose[11] # Left shoulder
        dist = distance(middle_tip, shoulder)
        if dist < touch_threshold:
            return True, min(95.0, 75.0 + (20.0 * (1.0 - dist / touch_threshold)))
            
    return False, 0.0
