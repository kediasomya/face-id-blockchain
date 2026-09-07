"""
Face detection and encoding module using OpenCV.
Detects faces in images and generates embeddings for blockchain storage.
"""

import cv2
import numpy as np
import logging
from pathlib import Path
from typing import List, Tuple, Dict
import hashlib

logger = logging.getLogger(__name__)


class FaceDetector:
    """Detects and encodes faces from images using OpenCV."""
    
    def __init__(self, min_face_size: int = 20, confidence_threshold: float = 0.6):
        """
        Initialize face detector.
        
        Args:
            min_face_size: Minimum face size in pixels
            confidence_threshold: Minimum confidence for face detection
        """
        self.min_face_size = min_face_size
        self.confidence_threshold = confidence_threshold
        logger.info("OpenCV Face Detector initialized")
    
    def load_image(self, image_path: str) -> np.ndarray:
        """Load image from file using OpenCV."""
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not read image: {image_path}")
        
        # Convert BGR to RGB
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        logger.info(f"Loaded image: {image_path}, shape: {image.shape}")
        return image
    
    def detect_faces(self, image: np.ndarray) -> List[Dict]:
        """
        Detect face-like regions using adaptive color and edge detection.
        This works on any face-like drawing or photo.
        
        Returns:
            List of face detections with bounding boxes
        """
        h, w, _ = image.shape
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        
        # Apply adaptive histogram equalization
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        # Detect edges
        edges = cv2.Canny(enhanced, 30, 100)
        
        # Apply morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        morph = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        face_locations = []
        for contour in contours:
            area = cv2.contourArea(contour)
            x, y, w, h = cv2.boundingRect(contour)
            
            # Filter by aspect ratio and size (face-like proportions)
            if h > 0 and w > 0:
                aspect_ratio = w / h
                # Faces are roughly square-ish (0.5 to 2.0 aspect ratio)
                if (0.4 < aspect_ratio < 2.5 and 
                    min(w, h) >= self.min_face_size and 
                    area > self.min_face_size * self.min_face_size):
                    
                    face_locations.append({
                        "bbox": (y, x + w, y + h, x),  # top, right, bottom, left
                        "confidence": min(0.85, aspect_ratio)  # Simple confidence
                    })
        
        # If no faces found with edge detection, try simpler approach
        if not face_locations:
            # Look for circular/oval regions
            circles = cv2.HoughCircles(
                gray,
                cv2.HOUGH_GRADIENT,
                dp=1,
                minDist=100,
                param1=50,
                param2=30,
                minRadius=self.min_face_size,
                maxRadius=min(h, w) // 2
            )
            
            if circles is not None:
                circles = np.uint16(np.around(circles))
                for circle in circles[0, :]:
                    x, y, r = circle
                    face_locations.append({
                        "bbox": (y - r, x + r, y + r, x - r),  # top, right, bottom, left
                        "confidence": 0.75
                    })
        
        logger.info(f"Detected {len(face_locations)} face(s)")
        return face_locations
    
    def extract_face_encoding(self, image: np.ndarray, bbox: Tuple[int, int, int, int]) -> np.ndarray:
        """
        Extract and create encoding from face bounding box.
        Uses histogram of face region and pixel values for encoding.
        
        Returns:
            Face encoding vector (512-dimensional feature vector)
        """
        top, right, bottom, left = bbox
        
        # Ensure coordinates are within bounds
        top = max(0, top)
        left = max(0, left)
        bottom = min(image.shape[0], bottom)
        right = min(image.shape[1], right)
        
        face_roi = image[top:bottom, left:right]
        
        if face_roi.size == 0:
            # Return zero vector if ROI is invalid
            return np.zeros(512)
        
        # Resize to standard size for consistent encoding
        face_resized = cv2.resize(face_roi, (128, 128))
        
        # Create multi-scale encoding
        encodings = []
        
        # 1. Color histogram (3 channels x 32 bins each)
        for i in range(3):  # RGB channels
            hist = cv2.calcHist([face_resized], [i], None, [32], [0, 256])
            encodings.append(hist.flatten())
        
        # 2. Grayscale histogram (64 bins)
        gray_face = cv2.cvtColor(face_resized, cv2.COLOR_RGB2GRAY)
        gray_hist = cv2.calcHist([gray_face], [0], None, [64], [0, 256])
        encodings.append(gray_hist.flatten())
        
        # 3. Edge detection histogram (32 bins)
        edges = cv2.Canny(gray_face, 50, 150)
        edge_hist = cv2.calcHist([edges], [0], None, [32], [0, 256])
        encodings.append(edge_hist.flatten())
        
        # 4. Downsampled pixel values at different scales
        for scale in [64, 32, 16]:
            resized = cv2.resize(face_resized, (scale, scale))
            # Flatten the RGB channels
            encodings.append(resized.flatten())
        
        # Concatenate all encodings
        encoding = np.concatenate(encodings)
        
        # Normalize
        norm = np.linalg.norm(encoding)
        if norm > 0:
            encoding = encoding / norm
        
        # Truncate to 512 dimensions
        if len(encoding) > 512:
            encoding = encoding[:512]
        elif len(encoding) < 512:
            # Pad with zeros if too short
            encoding = np.pad(encoding, (0, 512 - len(encoding)))
        
        return encoding
    
    def process_image(self, image_path: str) -> Dict:
        """
        Full pipeline: load image, detect faces, generate encodings.
        
        Returns:
            Dictionary with face data
        """
        try:
            image = self.load_image(image_path)
            face_locations = self.detect_faces(image)
            
            if not face_locations:
                logger.warning("No faces detected in image")
                return {"success": False, "error": "No faces detected"}
            
            # Extract encodings for all detected faces
            encodings = []
            for face in face_locations:
                encoding = self.extract_face_encoding(image, face["bbox"])
                encodings.append(encoding)
            
            # Use the first (primary) face
            primary_encoding = encodings[0]
            
            # Convert encoding to hashable format for blockchain
            encoding_hash = self._encode_to_hash(primary_encoding)
            
            return {
                "success": True,
                "num_faces": len(face_locations),
                "primary_face_encoding": primary_encoding.tolist()[:128],  # Store first 128 dims
                "encoding_hash": encoding_hash,
                "face_locations": [f["bbox"] for f in face_locations],
                "confidences": [f["confidence"] for f in face_locations],
                "image_shape": image.shape
            }
        
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _encode_to_hash(encoding: np.ndarray) -> str:
        """Convert face encoding to hashable hex string using SHA256."""
        # Ensure encoding is float and normalize to [0, 1]
        enc = np.array(encoding, dtype=np.float32)
        enc_min = enc.min()
        enc_max = enc.max()
        
        if enc_max > enc_min:
            enc = (enc - enc_min) / (enc_max - enc_min)
        
        # Quantize to bytes
        quantized = (enc * 255).astype(np.uint8)
        
        # Use SHA256 for consistent hashing
        hash_obj = hashlib.sha256(quantized.tobytes())
        return hash_obj.hexdigest()  # Return full 64-char SHA256 hash
