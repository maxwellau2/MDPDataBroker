import socket
import struct
import threading
import io
import time
import picamera
from multiprocessing import Process

# Constants
PACKET_SIZE = 1400  # UDP packet size < 1500 bytes (safe for most networks)
WIDTH, HEIGHT = 640, 480
FPS = 30

class ImageBroker:
    def __init__(self, udp_port: int, ip_address: str):
        self.udp_port = udp_port
        self.ip_address = ip_address
        self.running = False

        # Initialize UDP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Initialize PiCamera
        self.camera = picamera.PiCamera()
        self.camera.resolution = (WIDTH, HEIGHT)
        self.camera.framerate = FPS
        self.camera.start_preview()

        # Frame buffer
        self.frame_buffer = None
        self.lock = threading.Lock()

    def connect(self) -> int:
        """Simulate connection (always successful)."""
        print(f"Connecting to {self.ip_address}:{self.udp_port}")
        return 1  # Success

    def capture_frame(self):
        """Continuously capture frames and store them in a buffer."""
        stream = io.BytesIO()
        for _ in self.camera.capture_continuous(stream, format='jpeg', use_video_port=True):
            if not self.running:
                break

            with self.lock:
                self.frame_buffer = stream.getvalue()

            # Reset stream for the next frame
            stream.seek(0)
            stream.truncate()

    def send_frames(self):
        """Continuously send the latest frame from the buffer over UDP in chunks."""
        while self.running:
            with self.lock:
                if self.frame_buffer:
                    frame_data = self.frame_buffer
                else:
                    continue  # No frame available yet

            try:
                # Send frame size first
                self.sock.sendto(struct.pack("!I", len(frame_data)), (self.ip_address, self.udp_port))

                # Split frame into smaller packets
                for i in range(0, len(frame_data), PACKET_SIZE):
                    self.sock.sendto(frame_data[i:i + PACKET_SIZE], (self.ip_address, self.udp_port))
                    
            except OSError as e:
                print(f"Socket error: {e}")

            time.sleep(1 / FPS)  # Maintain FPS timing

    def run_until_death(self):
        """Start capturing and sending frames in separate threads."""
        self.running = True
        capture_thread = threading.Thread(target=self.capture_frame)
        send_thread = threading.Thread(target=self.send_frames)

        capture_thread.start()
        send_thread.start()

        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Stopping stream...")
            self.stop()
        finally:
            capture_thread.join()
            send_thread.join()

    def stop(self):
        """Stop streaming and release resources."""
        print("Releasing camera and socket resources...")
        self.running = False
        self.camera.close()
        self.sock.close()


class ImageBrokerRunner:
    def __init__(self, udp_port: int, ip_address: str):
        self.udp_port = udp_port
        self.ip_address = ip_address

    def run_broker_in_process(self):
        image_broker = ImageBroker(udp_port=self.udp_port, ip_address=self.ip_address)
        image_broker.connect()
        image_broker.run_until_death()



if __name__ == "__main__":
    import config
    # image_broker = ImageBroker(udp_port=9999, ip_address="192.168.24.20")
    # image_broker.connect()
    # image_broker.run_until_death()

    runner = ImageBrokerRunner(udp_port=9999, ip_address=config.UDP_IP)
    proc = Process(target=runner.run_broker_in_process)
    proc.start()
    proc.join()

# import socket
# import struct
# import time
# from io import BytesIO
# from picamera import PiCamera
# import threading
# from threading import Thread, Event
# from config import *

# class ImageBroker:
#     def __init__(self):
#         """Initialize the ImageBroker with camera streaming capabilities"""
#         # Network settings
#         self.udp_ip = UDP_IP
#         self.udp_port = UDP_PORT
#         self.packet_size = 8192
#         self.max_retries = 3
        
#         # Initialize camera and socket
#         self.setup_socket()
#         self.setup_camera()
        
#         # Threading control
#         self.running = False
#         self.stream_thread = None
#         self.stop_event = Event()
        
#         print("[IMAGE] Broker initialized")
        
#     def setup_socket(self):
#         """Set up UDP socket with improved buffer size and timeout"""
#         self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#         self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 2**20)
#         self.sock.settimeout(0.1)
        
#     def setup_camera(self):
#         """Initialize and configure the camera with optimal settings"""
#         self.camera = PiCamera()
#         self.camera.resolution = (640, 480)
#         self.camera.framerate = 30
#         self.camera.brightness = 50
#         self.camera.contrast = 50
#         self.camera.exposure_mode= "sports"
#         time.sleep(2)  # Wait for camera to warm up
#         print("[IMAGE] Camera configured")
        
#     def send_frame(self, frame_data):
#         """Send a frame with retry mechanism and error handling"""
#         retries = 0
#         while retries < self.max_retries and not self.stop_event.is_set():
#             try:
#                 # Send frame size
#                 size_data = struct.pack("!I", len(frame_data))
#                 self.sock.sendto(size_data, (self.udp_ip, self.udp_port))
                
#                 # Send frame in chunks
#                 for i in range(0, len(frame_data), self.packet_size):
#                     if self.stop_event.is_set():
#                         return False
#                     chunk = frame_data[i:i + self.packet_size]
#                     self.sock.sendto(chunk, (self.udp_ip, self.udp_port))
#                 return True
                
#             except socket.error as e:
#                 print(f"[IMAGE] Socket error: {e}, retry {retries + 1}/{self.max_retries}")
#                 retries += 1
#                 if retries < self.max_retries:
#                     time.sleep(0.1)
                    
#                 # Try to recreate socket on last retry
#                 if retries == self.max_retries - 1:
#                     print("[IMAGE] Recreating socket connection...")
#                     self.sock.close()
#                     self.setup_socket()
                    
#         return False
        
#     def stream_video(self):
#         """Main video streaming loop with FPS monitoring"""
#         print(f"[IMAGE] Starting stream to {self.udp_ip}:{self.udp_port}")
#         stream = BytesIO()
#         # frame_count = 0
#         # last_time = time.time()
#         # fps_counter = 0
        
#         try:
#             for _ in self.camera.capture_continuous(stream, format='jpeg', use_video_port=True, quality=80):
#                 if self.stop_event.is_set():
#                     break
                    
#                 # # Monitor FPS
#                 # current_time = time.time()
#                 # fps_counter += 1
#                 # if current_time - last_time >= 5:
#                 #     fps = fps_counter / (current_time - last_time)
#                 #     print(f"[IMAGE] Current FPS: {fps:.2f}")
#                 #     fps_counter = 0
#                 #     last_time = current_time
                
#                 # Send frame
#                 frame_data = stream.getvalue()
#                 if not self.send_frame(frame_data):
#                     print("[IMAGE] Failed to send frame after max retries")
#                     if self.stop_event.is_set():
#                         break
                
#                 # Reset stream for next frame
#                 stream.seek(0)
#                 stream.truncate()
#                 # frame_count += 1
                
#                 # Small delay to prevent overwhelming the network
                
#         except Exception as e:
#             print(f"[IMAGE] Streaming error: {e}")
#         finally:
#             self.cleanup()
            
#     def start(self):
#         """Start the video streaming thread"""
#         if not self.running:
#             self.running = True
#             self.stop_event.clear()
#             self.stream_thread = Thread(target=self.stream_video)
#             self.stream_thread.start()
#             print("[IMAGE] Streaming thread started")
            
#     def stop(self):
#         """Stop the video streaming thread gracefully"""
#         if self.running:
#             print("[IMAGE] Stopping stream...")
#             self.stop_event.set()
#             self.running = False
#             if self.stream_thread and self.stream_thread.is_alive():
#                 self.stream_thread.join()
#             self.cleanup()
            
#     def cleanup(self):
#         """Clean up resources"""
#         try:
#             self.camera.close()
#         except Exception as e:
#             print(f"[IMAGE] Error closing camera: {e}")
            
#         try:
#             self.sock.close()
#         except Exception as e:
#             print(f"[IMAGE] Error closing socket: {e}")
        
#         print("[IMAGE] Cleanup completed")

#     def run_broker_in_process(self):
#         """Run the broker in a separate process"""
#         try:
#             self.start()
#             while self.running:
#                 time.sleep(0.1)
#         except KeyboardInterrupt:
#             print("[IMAGE] Interrupted by user")
#         finally:
#             self.stop()


# class ImageBrokerRunner:
#     def __init__(self, udp_port: int, ip_address: str):
#         self.udp_port = udp_port
#         self.ip_address = ip_address

#     def run_broker_in_process(self):
#         image_broker = ImageBroker()
#         image_broker.udp_port = self.udp_port
#         image_broker.udp_ip = self.ip_address
#         image_broker.run_broker_in_process()


# if __name__ == "__main__":
#     runner = ImageBrokerRunner(udp_port=UDP_PORT, ip_address=UDP_IP)
#     proc = Thread(target=runner.run_broker_in_process)
#     proc.start()
#     proc.join()