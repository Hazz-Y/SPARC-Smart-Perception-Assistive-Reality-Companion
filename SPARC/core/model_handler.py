import os
import joblib
import logging
import string
import numpy as np
import pandas as pd
from SPARC.config.settings import GESTURE_MODELS

logger = logging.getLogger(__name__)

# Label Definitions
ISL_ALPHABET = ['1', '2', '3', '4', '5', '6', '7', '8', '9'] + list(string.ascii_uppercase)
ASL_NUMBERS_LABELS = ['1', '2', '3', '4', '5', '6', '7', '8', '9']
ASL_CHARACTERS_LABELS = list(string.ascii_uppercase)



class ModelHandler:
    def __init__(self, language_mode='ISL'):
        self.language_mode = language_mode
        self.isl_model = None
        self.asl_numbers_model = None
        self.asl_characters_model = None

        
        self.isl_label_map = ISL_ALPHABET
        self.asl_num_map = ASL_NUMBERS_LABELS
        self.asl_char_map = ASL_CHARACTERS_LABELS


        self._load_models()

    def _load_models(self):


        # Load Language Specific Models
        if self.language_mode == 'ISL':
            isl_path = GESTURE_MODELS.get('isl')
            if isl_path and os.path.exists(isl_path):
                try:
                    from tensorflow import keras
                    self.isl_model = keras.models.load_model(isl_path)
                    logger.info(f"Loaded ISL model from {isl_path}")
                except Exception as e:
                    logger.error(f"Failed to load ISL model: {e}")
            else:
                logger.error(f"ISL model not found at {isl_path}")
        
        elif self.language_mode == 'ASL':
            # ASL Numbers
            asl_num_path = GESTURE_MODELS.get('asl_numbers')
            if asl_num_path and os.path.exists(asl_num_path):
                try:
                    self.asl_numbers_model = joblib.load(asl_num_path)
                    logger.info(f"Loaded ASL numbers model from {asl_num_path}")
                except Exception as e:
                    logger.error(f"Failed to load ASL numbers model: {e}")
            
            # ASL Characters
            asl_char_path = GESTURE_MODELS.get('asl_character')
            if asl_char_path and os.path.exists(asl_char_path):
                try:
                    self.asl_characters_model = joblib.load(asl_char_path)
                    logger.info(f"Loaded ASL characters model from {asl_char_path}")
                except Exception as e:
                    logger.error(f"Failed to load ASL characters model: {e}")

    def predict_isl(self, data):
        """Returns (label, probability)"""
        if not self.isl_model:
            return None, 0.0
        try:
            df = pd.DataFrame([data])
            predictions = self.isl_model.predict(df, verbose=0)
            idx = np.argmax(predictions, axis=1)[0]
            prob = np.max(predictions)
            if idx < len(self.isl_label_map):
                return self.isl_label_map[idx], prob
        except Exception as e:
            logger.error(f"ISL Prediction error: {e}")
        return None, 0.0

    def predict_asl_numbers(self, data):
        if not self.asl_numbers_model:
            return None, 0.0
        try:
            df = pd.DataFrame([data])
            predictions = self.asl_numbers_model.predict_proba(df)
            idx = np.argmax(predictions, axis=1)[0]
            prob = np.max(predictions)
            if idx < len(self.asl_num_map):
                return self.asl_num_map[idx], prob
        except Exception as e:
            logger.error(f"ASL Numbers Prediction error: {e}")
        return None, 0.0

    def predict_asl_characters(self, data):
        if not self.asl_characters_model:
            return None, 0.0
        try:
            df = pd.DataFrame([data])
            predictions = self.asl_characters_model.predict_proba(df)
            idx = np.argmax(predictions, axis=1)[0]
            prob = np.max(predictions)
            if idx < len(self.asl_char_map):
                return self.asl_char_map[idx], prob
        except Exception as e:
            logger.error(f"ASL Characters Prediction error: {e}")
        return None, 0.0

