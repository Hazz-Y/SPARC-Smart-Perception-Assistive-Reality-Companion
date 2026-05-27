"""
Hand and touch-based gesture detection.
"""
import numpy as np
from ..utils import distance

def detect_cheek_gesture(results):
    """Detect index finger on right cheek."""
    if not results.face_landmarks or not results.right_hand_landmarks:
        return False, 0.0
        
    face = results.face_landmarks.landmark
    hand = results.right_hand_landmarks.landmark
    
    # Right cheek center (approx from 234, 454, 264)
    cheek_center_x = (face[234].x + face[454].x + face[264].x) / 3
    cheek_center_y = (face[234].y + face[454].y + face[264].y) / 3
    
    index_tip = hand[8]
    
    dist_x = abs(index_tip.x - cheek_center_x)
    dist_y = abs(index_tip.y - cheek_center_y)
    
    if dist_x < 0.08 and dist_y < 0.08 and index_tip.y < hand[5].y: # Extended
        max_dist = 0.08
        actual = (dist_x + dist_y) / 2
        conf = max(0.5, 1.0 - (actual / max_dist)) * 100
        return True, conf
        
    return False, 0.0

def detect_female_gesture(results):
    """Detect 'Female' (Blue hand touching nose)."""
    if not results.left_hand_landmarks or not results.face_landmarks:
        return False, 0.0
        
    hand = results.left_hand_landmarks.landmark
    nose_tip = results.face_landmarks.landmark[4]
    
    touch_points = [hand[4], hand[8], hand[12]] # Thumb, Index, Middle
    min_dist = min(distance(p, nose_tip) for p in touch_points)
    
    touch_threshold = 0.04
    if min_dist < touch_threshold:
        return True, min(95.0, 75.0 + (20.0 * (1.0 - min_dist / touch_threshold)))
        
    return False, 0.0

def detect_male_gesture(results):
    """Detect 'Male' (Blue hand touching lips)."""
    if not results.left_hand_landmarks or not results.face_landmarks:
        return False, 0.0
        
    hand = results.left_hand_landmarks.landmark
    face = results.face_landmarks.landmark
    
    # Lip center (between upper 13 and lower 14)
    lip_center_x = (face[13].x + face[14].x) / 2
    lip_center_y = (face[13].y + face[14].y) / 2
    lip_center = type('obj', (object,), {'x': lip_center_x, 'y': lip_center_y})
    
    touch_points = [hand[4], hand[8], hand[12]]
    min_dist = min(distance(p, lip_center) for p in touch_points)
    
    touch_threshold = 0.04
    if min_dist < touch_threshold:
         return True, min(95.0, 75.0 + (20.0 * (1.0 - min_dist / touch_threshold)))
         
    return False, 0.0

def detect_thank_you_gesture(results):
    """Detect 'Thank You' (Blue hand touching chin)."""
    if not results.left_hand_landmarks or not results.face_landmarks:
         return False, 0.0
         
    hand = results.left_hand_landmarks.landmark
    chin = results.face_landmarks.landmark[152] # Chin tip (152 is central chin)
    
    touch_points = [hand[4], hand[8], hand[12]]
    min_dist = min(distance(p, chin) for p in touch_points)
    
    touch_threshold = 0.04
    if min_dist < touch_threshold:
        return True, min(95.0, 75.0 + (20.0 * (1.0 - min_dist / touch_threshold)))
        
    return False, 0.0

def detect_doctor_gesture(results):
    """Detect 'Doctor' (Blue hand touching shoulder width region)."""
    if not results.left_hand_landmarks or not results.pose_landmarks:
        return False, 0.0
        
    hand = results.left_hand_landmarks.landmark
    pose = results.pose_landmarks.landmark
    
    left_shoulder = pose[11]
    right_shoulder = pose[12]
    
    shoulder_width = distance(left_shoulder, right_shoulder)
    if shoulder_width < 0.05: return False, 0.0
    
    shoulder_baseline_y = (left_shoulder.y + right_shoulder.y) / 2
    
    hand_points = [hand[4], hand[8], hand[12], hand[0]]
    
    min_dist = float('inf')
    detected = False
    
    threshold = 0.15 * shoulder_width
    vert_tolerance = 0.10 * shoulder_width
    
    for p in hand_points:
        dist_l = distance(p, left_shoulder)
        dist_r = distance(p, right_shoulder)
        height_diff = abs(p.y - shoulder_baseline_y)
        
        if (dist_l < threshold or dist_r < threshold) and height_diff < vert_tolerance:
            min_dist = min(min_dist, min(dist_l, dist_r))
            detected = True
        elif (min(left_shoulder.x, right_shoulder.x) <= p.x <= max(left_shoulder.x, right_shoulder.x)):
             if height_diff < vert_tolerance:
                 min_dist = min(min_dist, height_diff)
                 detected = True
                 
    if detected:
        return True, min(95.0, 75.0 + (20.0 * (1.0 - min_dist / threshold)))
        
    return False, 0.0

def detect_water_gesture(results):
    """Detect 'Water' (Green hand inside mouth)."""
    if not results.right_hand_landmarks or not results.face_landmarks:
        return False, 0.0
        
    hand = results.right_hand_landmarks.landmark
    face = results.face_landmarks.landmark
    
    # Mouth bounds
    upper_lip_y = face[13].y
    lower_lip_y = face[14].y
    # Mouth corners for width
    mouth_left_x = face[61].x  # Left corner
    mouth_right_x = face[291].x # Right corner
    mouth_center_x = (mouth_left_x + mouth_right_x) / 2
    mouth_center_y = (upper_lip_y + lower_lip_y) / 2

    # Points to check (fingertips + wrist)
    points = [hand[4], hand[8], hand[12], hand[16], hand[20], hand[0]]
    
    inside_count = 0
    min_dist = float('inf')
    
    for p in points:
        # Check inside box
        if (mouth_left_x <= p.x <= mouth_right_x) and (upper_lip_y <= p.y <= lower_lip_y):
            inside_count += 1
            
        # Check distance to center
        dist = np.sqrt((p.x - mouth_center_x)**2 + (p.y - mouth_center_y)**2)
        if dist < 0.05:
            inside_count += 1
            min_dist = min(min_dist, dist)
            
    if inside_count >= 1:
        return True, min(95.0, 70.0 + (25.0 * (inside_count / len(points))))

    return False, 0.0

def detect_both_palms_forward(results):
    """Detect both palms forward."""
    if not results.left_hand_landmarks or not results.right_hand_landmarks:
        return False, 0.0
        
    left = results.left_hand_landmarks.landmark
    right = results.right_hand_landmarks.landmark
    
    # Check wrists behind fingers (palm forward)
    # Z coordinate: lower is closer to camera. 
    # If palm is forward, wrist should be "behind" fingers (higher Z)? 
    # Wait, MediaPipe hand coords: Z decreases as you move towards camera.
    # So if palm forward, fingers are closer (smaller Z) than wrist (larger Z).
    # Original code: wrist.z > middle_mcp.z
    
    l_wrist_behind = left[0].z > left[9].z
    r_wrist_behind = right[0].z > right[9].z
    
    # Fingers extended (y check)
    l_ext = all(left[tip].y < left[base].y for tip, base in [(8, 5), (12, 9), (16, 13)])
    r_ext = all(right[tip].y < right[base].y for tip, base in [(8, 5), (12, 9), (16, 13)])
    
    if l_wrist_behind and r_wrist_behind and l_ext and r_ext:
        return True, 85.0
        
    return False, 0.0

def detect_simple_hand_signs(results):
    """
    Detect simple static hand signs: 
    Thumbs Up/Down, Ok, Hello.
    Returns: (gesture_name, confidence)
    """
    left_detected = results.left_hand_landmarks is not None
    right_detected = results.right_hand_landmarks is not None
    
    if not left_detected and not right_detected:
        return None, 0.0
        
    l_thumb_up = False
    r_thumb_up = False
    l_thumb_down = False
    r_thumb_down = False
    l_palm_up = False
    r_palm_up = False
    
    if left_detected:
        l = results.left_hand_landmarks.landmark
        l_thumb_up = l[4].y < l[3].y and l[4].y < l[2].y
        l_thumb_down = l[4].y > l[3].y and l[4].y > l[2].y
        l_palm_up = l[0].y > l[9].y
        
    if right_detected:
        r = results.right_hand_landmarks.landmark
        r_thumb_up = r[4].y < r[3].y and r[4].y < r[2].y
        r_thumb_down = r[4].y > r[3].y and r[4].y > r[2].y
        r_palm_up = r[0].y > r[9].y
        
    if l_thumb_down or r_thumb_down:
        return "thumbs_down", 85.0
    elif l_thumb_up and r_thumb_up:
        return "both_thumbs_up", 90.0
    elif l_thumb_up or r_thumb_up:
        return "one_thumb_up", 85.0
    elif l_palm_up or r_palm_up:
        return "palm_up", 85.0
        
    return None, 0.0
