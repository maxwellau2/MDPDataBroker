import socket
import struct
import threading
import io
import time
import picamera
from multiprocessing import Process

from GlobalVariableManager import GVL

# Constants
PACKET_SIZE = 1300  # UDP packet size < 1500 bytes (safe for most networks)
WIDTH, HEIGHT = 640, 480
FPS = 10

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
        GVL().logger.info(f"Connecting to {self.ip_address}:{self.udp_port}")
        # print(f"Connecting to {self.ip_address}:{self.udp_port}")
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
                GVL().logger.error(f"Socket error: {e}")

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
            GVL().logger.info("Keyboard interrupt, stopping stream")
            self.stop()
        finally:
            capture_thread.join()
            send_thread.join()

    def stop(self):
        """Stop streaming and release resources."""
        GVL().logger.info("Releasing camera and socket resources...")
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
