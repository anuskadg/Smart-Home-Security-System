import sys
import time
from gpiozero import MotionSensor, PWMOutputDevice

# Import custom modules
from camera_manager import CameraManager
from detector import ObjectDetector
from telegram_bot import TelegramBot
from config_loader import load_config

class SecuritySystem:
    def __init__(self, config_path='config.json'):
        """
        Initialize the Security System with configuration
        
        :param config_path: Path to the configuration JSON file
        """
        # Load configuration
        config = load_config(config_path)
        if not config:
            print("Failed to load configuration. Exiting.")
            sys.exit(1)
        
        # Extract Telegram credentials
        TELEGRAM_TOKEN = config['telegram']['token']
        TELEGRAM_CHAT_ID = config['telegram']['chat_id']
        
        # GPIO Configuration
        self.PIR_PIN = config['gpio']['pir_pin']
        self.BUZZER_PIN = config['gpio']['buzzer_pin']
        BUZZER_FREQUENCY = config['gpio'].get('buzzer_frequency', 2000)
        
        # Camera Configuration
        MODEL_PATH = config['camera']['model_path']
        VIDEO_DURATION = config['camera'].get('video_duration', 5)
        
        # Initialize GPIO devices
        self.pir_sensor = MotionSensor(self.PIR_PIN)
        self.buzzer = PWMOutputDevice(self.BUZZER_PIN, frequency=BUZZER_FREQUENCY)
        
        # Camera Setup
        self.camera_manager = CameraManager()
        
        # Initialize Object Detector
        self.detector = ObjectDetector(model_path=MODEL_PATH)
        
        # Initialize Telegram bot
        self.telegram_bot = TelegramBot(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)
        
        # Store video duration for use in run method
        self.VIDEO_DURATION = VIDEO_DURATION

    def buzz_buzzer(self, duration=1):
        """
        Activate buzzer for unauthorized access
        
        :param duration: Duration of buzzer sound in seconds
        """
        print("Access Denied - Activating Buzzer")
        self.buzzer.value = 0.5
        time.sleep(duration)
        self.buzzer.off()

    def handle_access_granted(self):
        """Handle authorized access scenario"""
        print("\n=== Access Granted - Door Open ===\n")

    def run(self):
        """
        Main security system loop with comprehensive motion detection and reporting
        """
        try:
            while True:
                print("Waiting for motion...")
                self.pir_sensor.wait_for_motion()
                print("Motion detected!")
                
                # Initialize paths to track files for cleanup
                h264_path = None
                image_path = None
                mp4_path = None
                annotated_image_path = None
                
                try:
                    # 1. Capture H.264 video
                    h264_path = self.camera_manager.capture_h264_video(duration=self.VIDEO_DURATION)
                    print(f"H.264 video captured: {h264_path}")
                    
                    # 2. Capture image
                    image, timestamp, image_path = self.camera_manager.capture_image()
                    print(f"Image captured: {image_path}")
                    
                    # 3. Perform object detection
                    detection_result, annotated_image_path = self.detector.detect_objects(image, timestamp)
                    print(f"Object detection completed. Annotated image: {annotated_image_path}")
                    
                    # 4. Determine action based on detection
                    if self.detector.check_access(detection_result):
                        self.handle_access_granted()
                    else:
                        self.buzz_buzzer()
                    
                    # 5. Convert H.264 to MP4
                    mp4_path = self.camera_manager.store_converted_video(h264_path)
                    print(f"Video converted to MP4: {mp4_path}")
                    
                    # 6. Send all to Telegram
                    # Send detection message
                    message = self.detector.format_detection_message(detection_result)
                    self.telegram_bot.send_message(message)
                    
                    # Send video
                    self.telegram_bot.send_video(mp4_path, caption="📹 Security Footage")
                    
                    # Send annotated image
                    if annotated_image_path:
                        self.telegram_bot.send_photo(annotated_image_path, caption="🔍 Detected Objects")
                    
                except Exception as e:
                    error_msg = f"Error in detection cycle: {str(e)}"
                    print(error_msg)
                    self.telegram_bot.send_message(f"❌ {error_msg}")
                
                finally:
                    # Cleanup files
                    self.camera_manager.cleanup_files(
                        video_paths=[h264_path, mp4_path] if h264_path or mp4_path else None, 
                        image_path=image_path
                    )
                    
                    # Remove annotated image
                    if annotated_image_path:
                        try:
                            self.detector.remove_annotated_image(annotated_image_path)
                        except Exception as cleanup_error:
                            print(f"Error removing annotated image: {cleanup_error}")
                    
                    # Ensure camera is cleaned up
                    self.camera_manager.cleanup()
                
                # Delay before next detection
                time.sleep(5)
                
        except KeyboardInterrupt:
            print("\nProgram interrupted by user")
        finally:
            # Final cleanup
            self.buzzer.close()
            self.camera_manager.cleanup()

def main():
    """
    Main entry point for the security system
    """
    try:
        security_system = SecuritySystem()
        security_system.run()
    except Exception as e:
        print(f"Critical error in security system: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()