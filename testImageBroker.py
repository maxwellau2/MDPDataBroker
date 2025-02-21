import cv2
import socket
import struct
import numpy as np

# Client settings
UDP_IP = "127.0.0.1"  # Listen for any sender
UDP_PORT = 9999
PACKET_SIZE = 4096

# Create UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1000000)  # 1MB Buffer
sock.bind((UDP_IP, UDP_PORT))

while True:
    # Receive frame size
    data, addr = sock.recvfrom(4)
    if not data:
        break
    frame_size = struct.unpack("!I", data)[0]

    # Receive frame data
    frame_data = b""
    while len(frame_data) < frame_size:
        packet, _ = sock.recvfrom(PACKET_SIZE)
        frame_data += packet

    # Decode and display frame
    frame = cv2.imdecode(np.frombuffer(frame_data, dtype=np.uint8), cv2.IMREAD_COLOR)
    if frame is not None:
        cv2.imshow("UDP Video Stream", frame)

    if cv2.waitKey(1) == ord('q'):
        break

sock.close()
cv2.destroyAllWindows()
