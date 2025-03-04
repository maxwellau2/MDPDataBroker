import socket
import json
from threading import Thread
from typing import Callable
from Broker import Broker
from GlobalVariableManager import GVL

class TCPClient(Broker):
    def __init__(self, server_host='127.0.0.1', server_port=12345):
        self.server_host = server_host
        self.server_port = server_port
        self.client_socket: socket.socket = None
        self.buffer = ""

    def connect(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client_socket.connect((self.server_host, self.server_port))
            return True
        except:
            return False
        
    def send(self, message):
        assert self.client_socket is not None, "client not connected"
        self.client_socket.sendall(message.encode('utf-8'))
        return
    
    def receive(self):
        """Receive messages and use a builder pattern to accumulate fragmented data."""
        assert self.client_socket is not None, "Client not connected, cannot receive"

        while True:
            chunk = self.client_socket.recv(1024).decode('utf-8')
            if not chunk:
                break  # No more data, message might be complete
            self.buffer += chunk  # Append to buffer
            
            # Try parsing as JSON (optional, if messages are JSON-based)
            try:
                message = json.loads(self.buffer)
                cpy = self.buffer
                self.buffer = ""  # Reset buffer after successful parse
                return cpy  # Return complete message
            except json.JSONDecodeError:
                continue  # Incomplete message, continue receiving

        return None  # No valid message received


    def run_until_death(self, callback: Callable[[str], None]):
        while True:
            message = self.receive()
            if message:
                if callback:
                    callback(message)

    def consume(self, message: dict):
        # print("LE MESSAGE", message)
        if "type" in message:
            if "path" == message["type"]:
                GVL().stm_instruction_list = message["data"]
                GVL().obstacleIdSequence = message["sequence"]
                GVL().coordinates = message["coordinates"]

                GVL().logger.debug(GVL().stm_instruction_list)
                GVL().logger.debug(GVL().obstacleIdSequence)
                GVL().logger.debug(GVL().coordinates)
            if "prediction-result" == message["type"]:
                GVL().predicted_image = message["data"]


    def send_message(self, message):
        """Connect to the server, send a message, and receive a response."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            try:
                client_socket.connect((self.server_host, self.server_port))
                # print(f"Connected to server at {self.server_host}:{self.server_port}")

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
    client = TCPClient(server_host='192.168.24.20', server_port=5000)
    client.connect()
    t1 = Thread(target=client.run_until_death, args=(print,))
    t1.start()
    client.send("predict")
#     client = TCPClient(server_host='192.168.24.40', server_port=4000)
#     client.connect()
#     t1 = Thread(target=client.run_until_death, args=(print,))
#     t1.start()
#     d = {'obstacles': [{'id': 2, 'x': 45, 'y': 125, 'orientation': 'N', 'imageId': 0}, {'id': 3, 'x': 135, 'y': 85, 'orientation': 'E', 'imageId': 0}, {'id': 1, 'x': 95, 'y': 45, 'orientation': 'N', 'imageId': 0}], 'robot': {'startPointX': 10, 'startPointY': 10, 'orientation': 'N'}}
#     client.send(json.dumps(d))
#     # client_socket.sendall(data.encode('utf-8'))
#     resp = client.send_message("predict")
#     print(resp)
    # client = TCPClient(server_host='192.168.24.20', server_port=6060)
    # data = {
    #         "from": "android",
    #         "msg": {
    #             "type": "algo-data",
    #             "data": {
    #             "obstacles": [
    #                 { "obstacleId": 1, "x": 15, "y": 185, "orientation": "S", "imageId": 1 },
    #                 { "obstacleId": 2, "x": 65, "y": 125, "orientation": "N", "imageId": 2 },
    #                 { "obstacleId": 3, "x": 85, "y": 75, "orientation": "E", "imageId": 3 },
    #                 { "obstacleId": 4, "x": 155, "y": 165, "orientation": "S", "imageId": 4 },
    #                 { "obstacleId": 5, "x": 195, "y": 95, "orientation": "W", "imageId": 5 }
    #             ],
    #             "robot": {
    #                 "startPointX": 0,
    #                 "startPointY": 0,
    #                 "orientation": "N"
    #             }
    #         }   
    #         }
    #         } 
    # d = json.dumps(data)
    # print(d)
    # # client_socket.sendall(data.encode('utf-8'))
    # client.send_message(d)
