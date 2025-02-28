import socket
import json

class TCPClient:
    def __init__(self, server_host='127.0.0.1', server_port=12345):
        self.server_host = server_host
        self.server_port = server_port

    def connect(self):
        pass

    def send_message(self, message):
        """Connect to the server, send a message, and receive a response."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            try:
                client_socket.connect((self.server_host, self.server_port))
                print(f"Connected to server at {self.server_host}:{self.server_port}")

                client_socket.sendall(message.encode('utf-8'))
                response = client_socket.recv(1024).decode('utf-8')
                print(f"Server response: {response}")

            except Exception as e:
                print(f"Connection error: {e}")
                response = "error"
            finally:
                client_socket.close()
        return response

if __name__ == "__main__":
    client = TCPClient(server_host='192.168.24.32', server_port=4000)
    data = {
            "from": "android",
            "msg": {
                "type": "algo-data",
                "data": {
                "obstacles": [
                    { "obstacleId": 1, "x": 15, "y": 185, "orientation": "S", "imageId": 1 },
                    { "obstacleId": 2, "x": 65, "y": 125, "orientation": "N", "imageId": 2 },
                    { "obstacleId": 3, "x": 85, "y": 75, "orientation": "E", "imageId": 3 },
                    { "obstacleId": 4, "x": 155, "y": 165, "orientation": "S", "imageId": 4 },
                    { "obstacleId": 5, "x": 195, "y": 95, "orientation": "W", "imageId": 5 }
                ],
                "robot": {
                    "startPointX": 0,
                    "startPointY": 0,
                    "orientation": "N"
                }
            }   
            }
            } 
    d = json.dumps(data)
    print(d)
    # client_socket.sendall(data.encode('utf-8'))
    client.send_message(d)
