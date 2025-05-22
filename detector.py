import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import warnings
import os

# Filter out the protobuf warning
warnings.filterwarnings('ignore', category=UserWarning, module='google.protobuf.symbol_database')

class ObjectDetector:
    def __init__(self, model_path, confidence_threshold=0.9, max_results=5):
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.max_results = max_results
        self.output_dir = 'images'
        self.ensure_directory()

    def ensure_directory(self):
        """Create output directory if it doesn't exist"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def detect_objects(self, image, timestamp):
        """Perform object detection on captured image"""
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)
        
        base_options = python.BaseOptions(model_asset_path=self.model_path)
        options = vision.ObjectDetectorOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.IMAGE,
            max_results=self.max_results,
            score_threshold=self.confidence_threshold
        )
        
        detector = vision.ObjectDetector.create_from_options(options)
        print("Performing object detection...")
        detection_result = detector.detect(mp_image)
        
        # Save annotated image
        annotated_image = self.draw_detections(image.copy(), detection_result)
        if len(detection_result.detections) > 0:
            annotated_path = os.path.join(
                self.output_dir, 
                f"detected_{timestamp}_{len(detection_result.detections)}objects.jpg"
            )
            cv2.imwrite(annotated_path, annotated_image)
        
        detector.close()
        
        return detection_result, annotated_path if len(detection_result.detections) > 0 else None

    def draw_detections(self, image, detection_result):
        """Draw detection boxes and labels on the image"""
        for detection in detection_result.detections:
            bbox = detection.bounding_box
            start_point = bbox.origin_x, bbox.origin_y
            end_point = bbox.origin_x + bbox.width, bbox.origin_y + bbox.height
            cv2.rectangle(image, start_point, end_point, (255, 0, 255), 3)

            category = detection.categories[0]
            category_name = category.category_name
            probability = round(category.score, 2)
            result_text = f"{category_name} ({probability})"
            
            text_location = (bbox.origin_x, bbox.origin_y - 10)
            cv2.putText(image, result_text, text_location, 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255), 2)
        return image

    def check_access(self, detection_result):
        """Check if access should be granted based on detection results"""
        if not detection_result.detections:
            print("No objects detected")
            return False
        
        # Check if any detection meets the confidence threshold
        for detection in detection_result.detections:
            confidence = detection.categories[0].score
            if confidence >= self.confidence_threshold:
                print(f"Authorized object detected with confidence: {confidence:.2%}")
                return True
        
        print("No authorized objects detected with sufficient confidence")
        return False

    def format_detection_message(self, detection_result):
        """Format detection results for Telegram message"""
        if len(detection_result.detections) == 0:
            return "🚫 No objects detected"
        
        message = "🔍 <b>Detection Results:</b>\n"
        for i, detection in enumerate(detection_result.detections, 1):
            category = detection.categories[0]
            confidence = category.score
            message += f"\n{i}. <b>{category.category_name}</b>"
            message += f"\n   Confidence: {confidence:.2%}"
            
            if confidence >= self.confidence_threshold:
                message += "\n   ✅ Access Granted - Door Open"
            else:
                message += "\n   ❌ Access Denied"
        return message

    def remove_annotated_image(self, annotated_image_path):
        """
        Remove the annotated image file
        
        :param annotated_image_path: Path to the annotated image to be removed
        """
        try:
            if annotated_image_path and os.path.exists(annotated_image_path):
                os.remove(annotated_image_path)
                print(f"Removed annotated image: {annotated_image_path}")
        except Exception as e:
            print(f"Error removing annotated image {annotated_image_path}: {e}")