"""
Utility functions for geometry and data calculations.
"""
import numpy as np

def distance(p1, p2):
    """
    Calculate Euclidean distance between two 3D points (landmarks).
    Supported types: MediaPipe Landmark objects (x, y, z) or simple objects with x, y attributes.
    """
    return np.sqrt((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2)

def calculate_angle(p1, p2, p3):
    """
    Calculate angle at p2 formed by p1-p2-p3 in degrees.
    """
    # Vector from p2 to p1
    v1 = np.array([p1.x - p2.x, p1.y - p2.y])
    # Vector from p2 to p3
    v2 = np.array([p3.x - p2.x, p3.y - p2.y])
    
    # Calculate angle using dot product
    dot_product = np.dot(v1, v2)
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    
    if norm1 == 0 or norm2 == 0:
        return 180.0  # Invalid angle
    
    cos_angle = np.clip(dot_product / (norm1 * norm2), -1.0, 1.0)
    angle_rad = np.arccos(cos_angle)
    angle_deg = np.degrees(angle_rad)
    
    return angle_deg

def get_shoulder_width(pose_landmarks):
    """
    Calculate shoulder width from pose landmarks.
    """
    left_shoulder = pose_landmarks[11]
    right_shoulder = pose_landmarks[12]
    return np.sqrt(
        (right_shoulder.x - left_shoulder.x) ** 2 + 
        (right_shoulder.y - left_shoulder.y) ** 2
    )
