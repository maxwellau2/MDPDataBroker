import socket

class TCPClient:
    def __init__(self, server_host='127.0.0.1', server_port=12345):
        self.server_host = server_host
        self.server_port = server_port

    def send_message(self, message):
        """Connect to the server, send a message, and receive a response."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            try:
                client_socket.connect((self.server_host, self.server_port))
                print(f"Connected to server at {self.server_host}:{self.server_port}")

                client_socket.send(message.encode('utf-8'))
                response = client_socket.recv(1024).decode('utf-8')
                print(f"Server response: {response}")

            except Exception as e:
                print(f"Connection error: {e}")
                response = "error"
            finally:
                client_socket.close()
        return response

if __name__ == "__main__":
    client = TCPClient()
    client.send_message("Hello, Server!")
