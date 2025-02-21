import socket
import struct
import time
from io import BytesIO
from picamera import PiCamera

# Network settings
UDP_IP = "192.168.24.49"
UDP_PORT = 9999
PACKET_SIZE = 1400  # Max UDP packet size
MAX_RETRIES = 3

class CameraStreamer:
    def __init__(self):
        # Initialize UDP socket
        self.setup_socket()
        
        # Initialize camera
        self.camera = PiCamera()
        self.configure_camera()
        print("[RPI] Camera initialized")
        
    def setup_socket(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Set socket buffer size
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
        # Set socket timeout
        self.sock.settimeout(1.0)
        
    def configure_camera(self):
        # Configure camera settings
        self.camera.resolution = (640, 640)
        self.camera.framerate = 30
        # Add some camera settings for better quality
        self.camera.brightness = 50
        self.camera.contrast = 50
        print("[RPI] Camera configuration: Resolution=640x640, FPS=30")
        time.sleep(2)  # Wait for camera to warm up
        
    def send_frame(self, frame_data):
        retries = 0
        while retries < MAX_RETRIES:
            try:
                # Send frame size first
                size_data = struct.pack("!I", len(frame_data))
                self.sock.sendto(size_data, (UDP_IP, UDP_PORT))
                
                # Send frame data in chunks
                chunks_sent = 0
                for i in range(0, len(frame_data), PACKET_SIZE):
                    chunk = frame_data[i:i + PACKET_SIZE]
                    self.sock.sendto(chunk, (UDP_IP, UDP_PORT))
                    chunks_sent += 1
                
                return True
            except socket.error as e:
                print(f"[RPI] Socket error: {e}, retry {retries + 1}/{MAX_RETRIES}")
                retries += 1
                time.sleep(0.1)  # Wait before retrying
                
                # If socket seems broken, recreate it
                if retries == MAX_RETRIES - 1:
                    print("[RPI] Recreating socket connection...")
                    self.sock.close()
                    self.setup_socket()
                
        return False
            
    def start_streaming(self):
        print(f"[RPI] Starting stream to {UDP_IP}:{UDP_PORT}")
        stream = BytesIO()
        frame_count = 0
        last_time = time.time()
        fps_counter = 0
        
        try:
            for _ in self.camera.capture_continuous(stream, format='jpeg', use_video_port=True, quality=80):
                # Calculate FPS
                current_time = time.time()
                fps_counter += 1
                if current_time - last_time >= 5:  # Show FPS every 5 seconds
                    fps = fps_counter / (current_time - last_time)
                    print(f"[RPI] Current FPS: {fps:.2f}")
                    fps_counter = 0
                    last_time = current_time
                
                # Get the frame data
                frame_data = stream.getvalue()
                frame_count += 1
                
                # Send frame
                if not self.send_frame(frame_data):
                    print("[RPI] Failed to send frame after max retries, continuing...")
                
                # Reset stream for next frame
                stream.seek(0)
                stream.truncate()
                
                # Small delay to prevent overwhelming the network
                time.sleep(0.01)
                
        except KeyboardInterrupt:
            print("[RPI] Streaming stopped by user")
        except Exception as e:
            print(f"[RPI] Streaming error: {e}")
        finally:
            self.cleanup()
            
    def cleanup(self):
        print("[RPI] Cleaning up...")
        self.camera.close()
        self.sock.close()

if __name__ == "__main__":
    while True:
        try:
            streamer = CameraStreamer()
            streamer.start_streaming()
        except Exception as e:
            print(f"[RPI] Fatal error: {e}")
            print("[RPI] Restarting in 5 seconds...")
            time.sleep(5)
        except KeyboardInterrupt:
            print("[RPI] Stopped by user")
            break
