import socket

SERVER_IP = "192.168.24.20"  # Change to the server's IP
TCP_PORT = 5000

def send_command(command):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((SERVER_IP, TCP_PORT))
        client_socket.sendall(command.encode())
        
        # Receive response (predicted class)
        try:
            response = client_socket.recv(1024).decode()
            print(f"Prediction Response: {response}")
        except socket.error as e:
            print(f"[TCP ERROR] Failed to receive response: {e}")

# Example usage
while True:
    cmd = input("Enter command (predict/stop/exit): ").strip().lower()
    if cmd in ["predict", "stop", "exit"]:
        send_command(cmd)
    if cmd == "exit":
        break
