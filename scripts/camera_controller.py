#!/usr/bin/env python3
# This script runs on the Raspberry Pi to control the camera

import time
import os
import datetime
import requests
import threading
import io
import picamera
from flask import Flask, Response, send_from_directory

class CameraController:
    def __init__(self):
        self.camera = None
        self.is_streaming = False
        self.stream_thread = None
        self.captures_dir = "static/captures"
        self.api_url = "http://localhost:5000/api"
        self.stream_output = None
        self.stream_clients = []
        
        # Create captures directory if it doesn't exist
        if not os.path.exists(self.captures_dir):
            os.makedirs(self.captures_dir)
        
        # Initialize Flask app for streaming
        self.app = Flask(__name__)
        self.setup_routes()
    
    def setup_routes(self):
        """Set up Flask routes for camera streaming and image access"""
        @self.app.route('/stream')
        def stream():
            return Response(self.generate_frames(), 
                           mimetype='multipart/x-mixed-replace; boundary=frame')
        
        @self.app.route('/captures/<path:filename>')
        def serve_capture(filename):
            return send_from_directory(self.captures_dir, filename)
    
    def initialize_camera(self):
        """Initialize camera with multiple backend support"""
        if self.camera is not None:
            return True
        
        # Try PiCamera2 first (recommended for newer Raspberry Pi OS)
        if self._try_picamera2():
            return True
        
        # Try legacy PiCamera
        if self._try_picamera():
            return True
        
        # Try OpenCV as fallback
        if self._try_opencv():
            return True
        
        # Use mock camera for testing
        print("No camera backends available, using mock camera")
        self._setup_mock_camera()
        return True

    def _try_picamera2(self):
        """Try to initialize PiCamera2"""
        try:
            from picamera2 import Picamera2
            self.camera = Picamera2()
            self.camera.configure(self.camera.create_preview_configuration(main={"size": (640, 480)}))
            self.camera.start()
            self.camera_backend = "picamera2"
            print("PiCamera2 initialized successfully")
            return True
        except ImportError:
            print("PiCamera2 not available")
            return False
        except Exception as e:
            print(f"PiCamera2 initialization failed: {e}")
            return False

    def _try_picamera(self):
        """Try to initialize legacy PiCamera"""
        try:
            import picamera
            self.camera = picamera.PiCamera()
            self.camera.resolution = (640, 480)
            self.camera.framerate = 24
            time.sleep(2)  # Camera warm-up
            self.camera_backend = "picamera"
            print("Legacy PiCamera initialized successfully")
            return True
        except ImportError:
            print("Legacy PiCamera not available")
            return False
        except Exception as e:
            print(f"Legacy PiCamera initialization failed: {e}")
            return False

    def _try_opencv(self):
        """Try to initialize OpenCV camera"""
        try:
            import cv2
            self.camera = cv2.VideoCapture(0)
            if self.camera.isOpened():
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                self.camera_backend = "opencv"
                print("OpenCV camera initialized successfully")
                return True
            else:
                self.camera.release()
                self.camera = None
                return False
        except ImportError:
            print("OpenCV not available")
            return False
        except Exception as e:
            print(f"OpenCV camera initialization failed: {e}")
            return False

    def _setup_mock_camera(self):
        """Setup mock camera for testing"""
        class MockCamera:
            def __init__(self):
                self.is_recording = False
            
            def start_recording(self, *args, **kwargs):
                self.is_recording = True
            
            def stop_recording(self):
                self.is_recording = False
            
            def capture(self, *args, **kwargs):
                # Create a simple test image
                return self._create_test_image()
            
            def close(self):
                pass
            
            def _create_test_image(self):
                """Create a test image for mock camera"""
                try:
                    from PIL import Image, ImageDraw, ImageFont
                    import io
                    
                    # Create a simple test image
                    img = Image.new('RGB', (640, 480), color='lightblue')
                    draw = ImageDraw.Draw(img)
                    
                    # Add timestamp
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    draw.text((10, 10), f"Mock Camera - {timestamp}", fill='black')
                    draw.text((10, 450), "Test Image", fill='black')
                    
                    return img
                except ImportError:
                    print("PIL not available for mock camera")
                    return None
        
        self.camera = MockCamera()
        self.camera_backend = "mock"
        print("Mock camera initialized")
    
    def start_streaming(self):
        """Start camera streaming"""
        if not self.is_streaming:
            if not self.initialize_camera():
                return False
            
            self.is_streaming = True
            self.stream_output = io.BytesIO()
            
            print("Camera streaming started")
            self.log_event("camera", "streaming_started")
            return True
        return False
    
    def stop_streaming(self):
        """Stop camera streaming"""
        if self.is_streaming:
            self.is_streaming = False
            
            if self.camera:
                self.camera.close()
                self.camera = None
            
            print("Camera streaming stopped")
            self.log_event("camera", "streaming_stopped")
            return True
        return False
    
    def generate_frames(self):
        """Generate frames for streaming"""
        if not self.initialize_camera():
            return
        
        try:
            # Start streaming if not already started
            if not self.is_streaming:
                self.start_streaming()
            
            # Use continuous capture for streaming
            for frame in self.camera.capture_continuous(io.BytesIO(), format='jpeg', use_video_port=True):
                if not self.is_streaming:
                    break
                
                # Get the frame data
                frame.seek(0)
                frame_data = frame.read()
                
                # Yield the frame in MJPEG format
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n')
                
                # Reset the stream for the next frame
                frame.seek(0)
                frame.truncate()
        except Exception as e:
            print(f"Error generating frames: {e}")
            self.is_streaming = False
    
    def capture_image(self):
        """Capture an image and save it"""
        if not self.initialize_camera():
            return None
        
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"capture_{timestamp}.jpg"
            filepath = os.path.join(self.captures_dir, filename)
            
            self.camera.capture(filepath)
            print(f"Image captured: {filepath}")
            
            self.log_event("camera", "capture", filename)
            return filename
        except Exception as e:
            print(f"Error capturing image: {e}")
            return None
    
    def log_event(self, action, status, details=None):
        """Log an event to the web app"""
        try:
            data = {
                "action": action,
                "status": status,
                "user": "camera_system",
                "details": details if details else ""
            }
            
            response = requests.post(f"{self.api_url}/log", json=data)
            if response.status_code == 200:
                print(f"Event logged: {action} - {status}")
            else:
                print(f"Failed to log event: {response.status_code}")
        except Exception as e:
            print(f"Error logging event: {e}")
    
    def run_server(self, host='0.0.0.0', port=8080):
        """Run the Flask server for camera streaming"""
        print(f"Starting camera server on {host}:{port}")
        print(f"Access the stream at http://{host}:{port}/stream")
        self.app.run(host=host, port=port, threaded=True)

if __name__ == "__main__":
    controller = CameraController()
    
    # Start streaming in a separate thread
    streaming_thread = threading.Thread(target=controller.start_streaming)
    streaming_thread.daemon = True
    streaming_thread.start()
    
    # Run the Flask server
    controller.run_server()
