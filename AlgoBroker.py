import socket

class TCPClient:
    def __init__(self, server_host='127.0.0.1', server_port=12345):
        self.server_host = server_host
        self.server_port = server_port

    def check_connection(self):
        """Check if the server is reachable."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(2)  # Set timeout for quick response
                sock.connect((self.server_host, self.server_port))
            print(f"Connection to {self.server_host}:{self.server_port} successful.")
            return True
        except (socket.timeout, ConnectionRefusedError):
            print(f"Could not connect to {self.server_host}:{self.server_port}.")
            return False

    def send(self, message: str) -> str:
        """Connect to the server, send a message, and receive a response."""
        if not self.check_connection():
            print("Server is unreachable. Aborting message send.")
            return

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            try:
                client_socket.connect((self.server_host, self.server_port))
                print(f"Connected to server at {self.server_host}:{self.server_port}")

                client_socket.send(message.encode('utf-8'))
                response = client_socket.recv(1024).decode('utf-8')
                print(f"Server response: {response}")
                return response

            except Exception as e:
                print(f"Connection error: {e}")
                return "error"

if __name__ == "__main__":
    client = TCPClient()

    # Check connection before sending a message
    if client.check_connection():
        client.send_message("Hello, Server!")
