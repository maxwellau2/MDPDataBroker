from threading import Thread
import time
from typing import Callable
from Broker import Broker
from serial import Serial
from GlobalVariableManager import GVL
from config import *
import json

# need to adjust.?
COM_PORT = "COM5"
BAUD_RATE = 115200

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
            return response
        except socket.error as e:
            print(f"[TCP ERROR] Failed to receive response: {e}")

class STMBroker(Broker):
    def __init__(self, com_port=COM_PORT, baud_rate=BAUD_RATE):
        self.com_port = com_port
        self.baud_rate = baud_rate
        self.serial_conn = None
        # self.connect()
    def connect(self) -> int:
        try:
            self.serial_conn = Serial(self.com_port, self.baud_rate, timeout=1)
            GVL().logger.info(f"Connected to STM on {self.com_port}")
            return 1  # Success
        except Exception as e:
            print(f"Failed to connect: {e}")
            return -1  # Error
        
    def send(self, message: str) -> None:
        if self.serial_conn:
            #
            self.serial_conn.flush()
            self.serial_conn.write(message.encode())
            # print(f"Sent: {message}")

    def send_rot(self, message: str) -> None:
        # look last 3 letters
        numeric = float(message[2:])
        numeric_int = int(numeric * 88.5/90.0)
        if len(str(numeric_int)) < 3:
            self.send(message[0:2]+"0" + f"{numeric_int}")
        else:
            self.send(message[0:2] + f"{numeric_int}")

    def receive(self) -> str:
        if self.serial_conn:
            # ensure that message sent by STM is a string with the newline character '\n', else readline won't work lol
            # data = self.serial_conn.read_all().decode()
            # data = self.serial_conn.read_all().decode().strip()
            # self.serial_conn.flush()
            data = self.serial_conn.readline().decode()
            # print(f"Received: {data}")
            return data
        return ""
    
    def flush(self):
        self.serial_conn.flush()

    def close(self) -> None:
        if self.serial_conn:
            self.serial_conn.close()
            print("STM connection closed")
            return 1
        return 0
    
    def run_until_death(self, callback: Callable[[str], None] = None):
        while True:
            message = self.receive()
            if message:
                if callback:
                    callback(message)

    def consume(self, message: dict):
        # {
        #     "from" : "stm",
        #     "msg" : {
        #         type: "ack",
        #     }
        # }
        if "type" in message and "ack" == message["type"]:
            GVL().logger.debug("Acknowledgement received from STM")
            GVL().stm_ack = True
        pass


if __name__ == "__main__":
    broker = STMBroker(STM_PORT, STM_BAUD_RATE)

    # t1 = Thread(target=broker.run_until_death, args=(print,))
    # t1.start()
    broker.connect()
    while True:
        print("0. test command")
        print("1. straight movement")
        print("2. rotate")
        print("3. Navigate")
        res = input("enter case number: ")
        command = "FW010"
        command2 = "CF089"
        toSend = command
        
        if res == "0":
            command = input("enter command: ")
            broker.send(command)        

            while True:
                text = broker.receive()
                if text != "" and text is not None:
                    res = json.loads(text)
                    sender = res['from']
                    content = res['msg']
                    # use this to check
                    if "type" in content and "ack" == content["type"]:
                        print("DIUUUUUUUUUUUUU")
                    # if len(text) > 15:
                        print(text)
                        text = ""
                        break
                        
                
                # if len(text) > 15:
                #     if toSend == command:
                #         toSend = command2
                #     else:
                #         toSend = command
                #     print("Sending:" + toSend)
                #     broker.send(toSend)

        if res == "1":
            broker.send("FW110")
            break
            # while True:
            #     text = broker.receive()
            #     if text != "" and text is not None:
                    # break
        if res == "2":
            broker.send("AF180")
            # broker.send_rot("CF360")
            while True:
                text = broker.receive()
                if text != "" and text is not None:
                    break

        if res == "3":
            sleepTime = 0
            for i in range(0,4):
                time.sleep(sleepTime)
                cs = 0
                while cs != 70:
                    # broker.serial_conn.flush()
                    text = ""
                    if cs == 0:
                        # send command to move until x distance
                        broker.send("DT010")
                        print("in 0")

                        #Waiting for ACK from STM
                        while True:
                            text = broker.receive()
                            if len(text) > 15:
                                print(text)
                                break
                        # print(text, len(text), type(text))
                        time.sleep(sleepTime)
                        text = ""
                        cs = 20 #5

                    if cs == 5:
                        # perform prediction
                        result = send_command("predict")
                        print("Predicted")
                        if result == "Bullseye" or result == "No Detection":
                            cs = 20
                        else:
                            cs = 70
                            break
                        time.sleep(sleepTime)
                        
                    if cs == 10:
                        # back off
                        # broker.send("BW004")
                        # print("in 10")
                        # while text == "" or text is None:
                        #     text = broker.receive()
                        #     # print(text)
                        # print(text, len(text), type(text))
                        
                        # text = ""
                        cs = 20
                        broker.serial_conn.flush()
                        time.sleep(sleepTime)

                    if cs == 20:
                        # send the rotation bw A90
                        broker.send("CB087")
                        # broker.send("BA090\n") # always 90
                        print("in 20")

                        #Waiting for ACK from STM
                        while True:
                            text = broker.receive()
                            if len(text) > 15:
                                print(text)
                                break
                        # print(text, len(text), type(text))
                        
                        text = ""
                        cs = 30
                        broker.serial_conn.flush()
                        time.sleep(sleepTime)

                    if cs == 30:
                        # send the forward
                        broker.send("FW070")
                        print("in 30")
                        while True:
                            text = broker.receive()
                            if len(text) > 15:
                                print(text)
                                break
                        # print(text, len(text), type(text))
                        text = ""
                        cs = 40
                        broker.serial_conn.flush()
                        time.sleep(sleepTime)

                    if cs == 40:
                        # send the rotation 180 cw
                        broker.send("CF080")
                        print("in 40")
                        while True:
                            text = broker.receive()
                            if len(text) > 15:
                                print(text)
                                break
                        # print(text, len(text), type(text))
                        text = ""
                        cs = 50
                        broker.serial_conn.flush()
                        time.sleep(sleepTime)
                        # break
                    if cs == 50:
                        # send the rotation 180 cw
                        broker.send("FW007")
                        print("in 50")
                        while True:
                            text = broker.receive()
                            if len(text) > 15:
                                print(text)
                                break
                        # print(text, len(text), type(text))
                        text = ""
                        cs = 60
                        broker.serial_conn.flush()
                        time.sleep(sleepTime)
                        # break

                    if cs == 60:
                        # send the rotation 180 cw
                        broker.send("CF080")
                        print("in 60")
                        while True:
                            text = broker.receive()
                            if len(text) > 15:
                                print(text)
                                break
                        # print(text, len(text), type(text))
                        text = ""
                        cs = 70
                        broker.serial_conn.flush()
                        time.sleep(sleepTime)
                        break