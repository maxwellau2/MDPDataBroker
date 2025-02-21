import socket
import time

# Network settings
UDP_IP = "192.168.24.49"  # Your computer's IP
UDP_PORT = 9999

# Create socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

print(f"[TEST] Starting UDP test to {UDP_IP}:{UDP_PORT}")

# Send test messages
counter = 0
while True:
    try:
        message = f"Test message {counter}".encode()
        sock.sendto(message, (UDP_IP, UDP_PORT))
        print(f"[TEST] Sent message {counter}")
        counter += 1
        time.sleep(1)
    except KeyboardInterrupt:
        print("\n[TEST] Stopped by user")
        break
    except Exception as e:
        print(f"[TEST] Error: {e}")
        break

sock.close()
