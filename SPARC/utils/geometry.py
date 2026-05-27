import re
import math
import copy
import itertools
import numpy as np

def replace_multiple_spaces_with_single(sentence):
    """
    Replace multiple consecutive whitespace characters with a single space.
    """
    return re.sub(r'\s+', ' ', sentence).strip()

def calculate_angle(A, B, C):
    """
    Calculate the angle between three points A, B, and C.
    """
    BA = (A[0] - B[0], A[1] - B[1])
    BC = (C[0] - B[0], C[1] - B[1])
    magnitude_BA = math.sqrt(BA[0] ** 2 + BA[1] ** 2)
    magnitude_BC = math.sqrt(BC[0] ** 2 + BC[1] ** 2)
    if magnitude_BA == 0 or magnitude_BC == 0:
        return 0.0
    cosine_angle = (BA[0] * BC[0] + BA[1] * BC[1]) / (magnitude_BA * magnitude_BC)
    cosine_angle = max(-1.0, min(1.0, cosine_angle))
    angle = math.degrees(math.acos(cosine_angle))
    return angle

def calculate_features(coords):
    """
    Calculate Euclidean distances between all pairs of coordinates.
    """
    distances = []
    for i in range(len(coords)):
        for j in range(i + 1, len(coords)):
            distance = np.linalg.norm(np.array(coords[i]) - np.array(coords[j]))
            distances.append(distance)
    return distances

def pre_process_landmark(landmark_list):
    """
    Preprocess landmarks: convert to relative coordinates and normalize.
    """
    temp_landmark_list = copy.deepcopy(landmark_list)
    
    # Convert to relative coordinates
    base_x, base_y = 0, 0
    for index, landmark_point in enumerate(temp_landmark_list):
        if index == 0:
            base_x, base_y = landmark_point[0], landmark_point[1]
        temp_landmark_list[index][0] = temp_landmark_list[index][0] - base_x
        temp_landmark_list[index][1] = temp_landmark_list[index][1] - base_y
    
    # Convert to a one-dimensional list
    temp_landmark_list = list(itertools.chain.from_iterable(temp_landmark_list))
    
    # Normalization
    max_value = max(list(map(abs, temp_landmark_list))) if temp_landmark_list else 1
    if max_value == 0:
        max_value = 1
    
    def normalize_(n):
        return n / max_value
    
    temp_landmark_list = list(map(normalize_, temp_landmark_list))
    return temp_landmark_list
