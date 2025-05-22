import time
import os
import cv2
from datetime import datetime
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder, Quality
import subprocess

class CameraManager:
    def __init__(self):
        self.picam2 = None
        self.encoder = H264Encoder()
        self._max_retries = 3
        self._retry_delay = 2  # seconds
        self.video_dir = 'videos'
        self.images_dir = 'images'
        self.ensure_directories()

    def ensure_directories(self):
        """Create necessary directories if they don't exist"""
        for directory in [self.video_dir, self.images_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)

    def initialize_camera(self, mode='preview'):
        """Initialize camera with retries and proper cleanup"""
        for attempt in range(self._max_retries):
            try:
                if self.picam2 is not None:
                    self.picam2.close()
                    time.sleep(1)  # Allow time for cleanup
                
                self.picam2 = Picamera2()
                
                if mode == 'preview':
                    self.picam2.preview_configuration.main.size = (640, 480)
                    self.picam2.preview_configuration.main.format = "RGB888"
                    self.picam2.preview_configuration.align()
                    self.picam2.configure("preview")
                elif mode == 'video':
                    self.picam2.configure(self.picam2.create_video_configuration())
                
                self.picam2.start()
                time.sleep(2)  # Warm-up time
                return True
                
            except Exception as e:
                print(f"Camera initialization attempt {attempt + 1} failed: {str(e)}")
                if attempt < self._max_retries - 1:
                    time.sleep(self._retry_delay)
                else:
                    raise RuntimeError(f"Failed to initialize camera after {self._max_retries} attempts")
    
    def cleanup(self):
        """Safely cleanup camera resources"""
        if self.picam2 is not None:
            try:
                self.picam2.stop()
                self.picam2.close()
            except Exception as e:
                print(f"Error during camera cleanup: {str(e)}")
            finally:
                self.picam2 = None

    def capture_h264_video(self, duration=5):
        """
        Capture video in H.264 format only
        
        :param duration: Length of video recording in seconds
        :return: Path to the captured H.264 video file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        h264_path = os.path.join(self.video_dir, f"video_{timestamp}.h264")
        
        try:
            self.initialize_camera(mode='video')
            
            print("Recording H.264 video...")
            self.picam2.start_recording(
                self.encoder, 
                h264_path, 
                quality=Quality.HIGH
            )
            time.sleep(duration)
            self.picam2.stop_recording()
            
            return h264_path
            
        except Exception as e:
            print(f"Error during H.264 video capture: {str(e)}")
            raise
        finally:
            self.cleanup()

    def convert_h264_to_mp4(self, h264_path, mp4_path=None):
        """
        Convert H.264 video to MP4 format
        
        :param h264_path: Path to the source H.264 video file
        :param mp4_path: Optional path for the output MP4 file. 
                         If not provided, generates a path based on the source file
        :return: Path to the converted MP4 video file
        """
        # If no MP4 path is provided, generate one based on the H.264 file path
        if mp4_path is None:
            mp4_path = h264_path.replace('.h264', '.mp4')
        
        command = f"ffmpeg -fflags +genpts -i {h264_path} -vf vflip -c:v h264 {mp4_path}"
        try:
            subprocess.run(command, shell=True, check=True)
            print(f"Converted and flipped video to {mp4_path}")
            return mp4_path
        except subprocess.CalledProcessError as e:
            print(f"Error during video conversion: {e}")
            raise

    def store_converted_video(self, h264_path):
        """
        Convert H.264 video to MP4 and store in videos directory
        
        :param h264_path: Path to the source H.264 video file
        :return: Path to the stored MP4 video file
        """
        try:
            # Generate MP4 path in the videos directory
            filename = os.path.basename(h264_path).replace('.h264', '.mp4')
            mp4_path = os.path.join(self.video_dir, filename)
            
            # Convert the video
            return self.convert_h264_to_mp4(h264_path, mp4_path)
        
        except Exception as e:
            print(f"Error storing converted video: {str(e)}")
            raise

    def capture_image(self):
        """Capture a single image from PiCamera2 with improved error handling"""
        try:
            self.initialize_camera(mode='preview')
            
            print("Capturing image...")
            image = self.picam2.capture_array()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            image = cv2.resize(image, (640, 480))
            image = cv2.flip(image, -1)
            
            # Save the image 
            image_path = os.path.join(self.images_dir, f"captured_{timestamp}.jpg")
            cv2.imwrite(image_path, image)
            
            return image, timestamp, image_path
            
        except Exception as e:
            print(f"Error during image capture: {str(e)}")
            raise
        finally:
            self.cleanup()

    def cleanup_files(self, video_paths=None, image_path=None):
        """
        Remove video and image files
        
        :param video_paths: List of video file paths to remove
        :param image_path: Path of image file to remove
        """
        if video_paths:
            for path in video_paths:
                try:
                    if os.path.exists(path):
                        os.remove(path)
                        print(f"Removed video file: {path}")
                except Exception as e:
                    print(f"Error removing video file {path}: {e}")
        
        if image_path:
            try:
                if os.path.exists(image_path):
                    os.remove(image_path)
                    print(f"Removed image file: {image_path}")
            except Exception as e:
                print(f"Error removing image file {image_path}: {e}")