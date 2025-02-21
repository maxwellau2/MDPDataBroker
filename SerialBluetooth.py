import time
from BluetoothStrategy import BluetoothStrategy
import platform

# check windows vs linux
# if platform.system() != "Windows":
#     raise RuntimeError(f"This class is only for Windows, you are on {platform.system()}")
import serial
import subprocess 

class SerialBluetooth(BluetoothStrategy):
    def __init__(self, com_port="COM5", baud_rate=115200):
        self.com_port = com_port
        self.baud_rate = baud_rate
        self.serial_conn = None

    def connect(self) -> int:
        try:
            # output = subprocess.call(['sudo', 'listenBluetooth.sh'])
            # time.sleep(5)
            self.serial_conn = serial.Serial(self.com_port, self.baud_rate, timeout=1)
            time.sleep(2)  # Allow connection time
            print(f"Connected to Bluetooth on {self.com_port}")
            return 1  # Success
        except Exception as e:
            print(f"Failed to connect: {e}")
            return -1  # Error

    def send(self, message: str) -> None:
        if self.serial_conn:
            self.serial_conn.write(message.encode())
            print(f"Sent: {message}")

    def receive(self) -> str:
        if self.serial_conn:
            data = self.serial_conn.readline().decode().strip()
            if data:
                print(f"Received: {data}")
                return data
        return ""

    def close(self) -> None:
        if self.serial_conn:
            self.serial_conn.close()
            print("Bluetooth connection closed (Serial Blutooth)")
