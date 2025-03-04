import bluetooth
import os
import json
import time
import subprocess
from typing import Callable
from Broker import Broker
from GlobalVariableManager import GVL

class AndroidBroker(Broker):
    def __init__(self):
        self.server_sock = None
        self.client_sock = None
        self.client_info = None
        self.uuid = "00001101-0000-1000-8000-00805F9B34FB"  # Unique service UUID

    def setup_server(self):
        """Sets up the Bluetooth server socket and makes it discoverable."""
        GVL().logger.info("Setting up Bluetooth server...")
        self.server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        self.server_sock.bind(("", 1))
        self.server_sock.listen(1)
        port = self.server_sock.getsockname()[1]

        bluetooth.advertise_service(
            self.server_sock, "MDP-Server",
            service_id=self.uuid,
            service_classes=[self.uuid, bluetooth.SERIAL_PORT_CLASS],
            profiles=[bluetooth.SERIAL_PORT_PROFILE],
        )

        GVL().logger.info(f"Bluetooth server started on RFCOMM channel {port}")
        print(f"Waiting for Bluetooth connection on channel {port}...")

    def connect(self) -> int:
        """Tries to establish a Bluetooth connection without unnecessary retries."""
        if self.client_sock:  # Prevent multiple connections
            GVL().logger.info("Bluetooth already connected. Skipping reconnection.")
            return 1

        max_retries = 6
        attempt = 0

        while attempt < max_retries:
            try:
                GVL().logger.info(f"Bluetooth connection attempt {attempt + 1}/{max_retries}")
                
                if attempt == 0:
                    self.cleanup()
                    self.restart_bluetooth()  # Only restart Bluetooth on the first attempt
                    self.setup_server()  # Start the Bluetooth server

                self.client_sock, self.client_info = self.server_sock.accept()
                GVL().logger.info(f"Accepted connection from {self.client_info}")
                print(f"Accepted connection from {self.client_info}")

                # GVL().logger.info(f"Stopping discovery {self.client_info}")
                # self.stop_discovery()

                return 1  # ✅ Success

            except bluetooth.BluetoothError as e:
                attempt += 1
                GVL().logger.warning(f"Bluetooth connection failed (Attempt {attempt}/{max_retries}): {e}")
                time.sleep(2)  # ⏳ Wait before retrying

        return self.connect()  # ❌ Failed after max retries, recursively try (LOL AHHAHAHAHAH)


    def send(self, message: str) -> None:
        """Sends a message to the connected Bluetooth client."""
        if self.client_sock:
            try:
                if isinstance(message, dict):
                    message = json.dumps(message)

                self.client_sock.send(message + "\n")
                GVL().logger.info(f"Sent to Android: {message}")
            except bluetooth.BluetoothError as e:
                GVL().logger.error(f"Failed to send message: {e}")

    def receive(self) -> str:
        """Receives a message from the connected Bluetooth client."""
        if self.client_sock:
            try:
                data = self.client_sock.recv(1024).decode().strip()
                if len(data) == 0:
                    print("Client disconnected.")
                    GVL().logger.warning("Client disconnected. Waiting for new connection...")
                    self.cleanup()  # Properly close the connection
                    self.connect()  # Reconnect
                    return ""

                GVL().logger.info(f"Received from Android: {data}")
                return data
            except bluetooth.BluetoothError as e:
                GVL().logger.error(f"Failed to receive message: {e}")
                self.cleanup()
                self.connect()  # Attempt to reconnect
            except IOError as e:
                GVL().logger.error(f"Failed to receive message: {e}")
                self.cleanup()
                self.connect()  # Attempt to reconnect
        return ""

    def close(self) -> None:
        """Closes the Bluetooth sockets properly."""
        if self.client_sock:
            self.client_sock.close()
            self.client_sock = None
            GVL().logger.info("Closed client socket")

    def run_until_death(self, callback: Callable[[str], None] = None):
        """Continuously polls for new data and calls the callback function."""
        while True:
            if not self.client_sock:  # Ensure a valid connection
                GVL().logger.warning("No active Bluetooth connection. Attempting to reconnect...")
                self.connect()

            message = self.receive()
            if message:
                if message == '''{"from":"android","msg":{"type":"heartbeat"}}''':
                    pass
                elif callback:
                    callback(message)

    def consume(self, message: dict):
        """Processes incoming messages and updates GVL state accordingly."""
        GVL().logger.debug(f"Android Broker received: {message}")
        if message.get("type") == "algo-data":
            # straight away give the data to the algo broker, dun wait
            GVL().android_has_sent_map = True
            GVL().android_map = message["data"]
            GVL().android_map_data = message["data"]
            # invoke the sending of map data to algo broker
            # make sure to reset the stm instruciton list to None
            GVL().stm_instruction_list = None
            print(message["data"])
            print("sending to algo broker")
            GVL().algo_broker.send(json.dumps(message))
            print("sent to algo broker")
            GVL().logger.info(f"Sent map data to broker {json.dumps(message)}")
            GVL().android_has_sent_map = True
            
        elif message.get("type") == "command":
            GVL().taskId = int(message["data"]["taskId"])
            GVL().start = message["data"]["instruction"] == "start"

    def cleanup(self):
        """Cleans up Bluetooth sockets before retrying."""
        if self.client_sock:
            try:
                self.client_sock.close()
                GVL().logger.info("Client socket closed for cleanup")
            except bluetooth.BluetoothError:
                pass
            self.client_sock = None

    def stop_discovery(self):
        os.system('echo -e "power on\ndiscoverable off\npairable off\nexit" | sudo bluetoothctl')
        return

    def restart_bluetooth(self):
        """Restarts Bluetooth synchronously and ensures it's discoverable."""
        GVL().logger.warning("Restarting Bluetooth and making it discoverable...")

        # Kill any processes using rfcomm
        os.system("sudo pkill -f rfcomm")
        
        # Restart Bluetooth service
        os.system("sudo systemctl restart bluetooth")
        time.sleep(2)

        # Ensure Bluetooth adapter is up
        os.system("sudo hciconfig hci0 up")
        os.system("sudo hciconfig hci0 piscan")

        # Optional: Use bluetoothctl as a fallback
        os.system('echo -e "power on\ndiscoverable on\npairable on\nexit" | sudo bluetoothctl')

        time.sleep(5)  # ⏳ Wait for Bluetooth to fully restart
        GVL().logger.warning("Bluetooth restart completed.")



    def send_scanning(self, position_x: int, position_y: int, orientation: str):
        data = {
                "from": "rpi",
                "msg": {
                "type": "status",
                "data": {
                        "nextAction": "scanning",
                        "currentPosition": {
                        "orientation": orientation,
                        "x": position_x,
                        "y": position_y
                        }
                    }
                }
            }
        self.send(data)

    def send_obstacle_image_found(self, position_x: int, position_y: int, orientation: str, obstacle_id: int, image_id: int):
        data = {
                "from": "rpi",
                "msg": {
                        "type": "status",
                        "data": {
                        "nextAction": "idle",
                        "currentPosition": {
                            "orientation": orientation,
                            "x": position_x,
                            "y": position_y
                        },
                        "target": {
                            "obstacleId": obstacle_id,
                            "imageId": image_id
                        }
                    }
                }
            }
        self.send(data)

    def send_idling(self, position_x: int, position_y: int, orientation: str):
        data = {
                "from": "rpi",
                "msg": {
                    "type": "status",
                    "data": {
                        "nextAction": "idle",
                        "currentPosition": {
                            "orientation": orientation,
                            "x": position_x,
                            "y": position_y
                        }
                    }
                }
            }
        self.send(data)

    def send_moving(self, position_x: int, position_y: int, orientation: str):
        data = {
                "from": "rpi",
                "msg": {
                    "type": "status",
                    "data": {
                        "nextAction": "moving",
                        "currentPosition": {
                            "orientation": orientation,
                            "x": position_x,
                            "y": position_y
                        }
                    }
                }
            }
        self.send(data)

    def send_finished(self, position_x: int, position_y: int, orientation: str):
        data = {
                "from": "rpi",
                "msg": {
                    "type": "status",
                    "data": {
                        "nextAction": "finished",
                        "currentPosition": {
                            "orientation": orientation,
                            "x": position_x,
                            "y": position_y
                        }
                    }
                }
            }
        self.send(data)

    def send_error(self, position_x: int, position_y: int, orientation: str):
        data = {
                "from": "rpi",
                "msg": {
                    "type": "status",
                    "data": {
                        "nextAction": "error",
                        "currentPosition": {
                            "orientation": orientation,
                            "x": position_x,
                            "y": position_y
                        }
                    }
                }
            }
        self.send(data)


if __name__ == "__main__":
    android = AndroidBroker()
    res = android.connect()
    if res:
        while True:
            data = android.receive()
            print(data)