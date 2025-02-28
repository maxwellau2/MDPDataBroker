# import bluetooth
# import os
# import json
# import time
# import subprocess
# from typing import Callable
# from Broker import Broker
# from GlobalVariableManager import GVL

# class AndroidBroker(Broker):
#     def __init__(self):
#         self.server_sock = None
#         self.client_sock = None
#         self.client_info = None
#         self.uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee"  # Unique service UUID

#     def connect(self) -> int:
#         """Tries to establish a Bluetooth connection without unnecessary retries."""
#         if self.client_sock:  # Prevent multiple connections
#             GVL().logger.info("Bluetooth already connected. Skipping reconnection.")
#             return 1
#         max_retries=6
#         attempt = 0
#         while attempt < max_retries:
#             try:
#                 GVL().logger.info(f"Bluetooth connection attempt {attempt + 1}/{max_retries}")

#                 self.cleanup()
#                 self.restart_bluetooth()

#                 self.server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
#                 self.server_sock.bind(("", bluetooth.PORT_ANY))
#                 self.server_sock.listen(1)
#                 port = self.server_sock.getsockname()[1]

#                 bluetooth.advertise_service(
#                     self.server_sock, "MDP-Server",
#                     service_id=self.uuid,
#                     service_classes=[self.uuid, bluetooth.SERIAL_PORT_CLASS],
#                     profiles=[bluetooth.SERIAL_PORT_PROFILE],
#                 )

#                 GVL().logger.info(f"Bluetooth server started on RFCOMM channel {port}")
#                 print(f"Waiting for Bluetooth connection on channel {port}...")

#                 self.client_sock, self.client_info = self.server_sock.accept()
#                 GVL().logger.info(f"Accepted connection from {self.client_info}")
#                 print(f"Accepted connection from {self.client_info}")

#                 return 1  # ✅ Success

#             except bluetooth.BluetoothError as e:
#                 attempt += 1
#                 GVL().logger.warning(f"Bluetooth connection failed (Attempt {attempt}/{max_retries}): {e}")
#                 time.sleep(2)  # ⏳ Wait before retrying

#         return 0  # ❌ Failed after max retries


#     def send(self, message: str) -> None:
#         """Sends a message to the connected Bluetooth client."""
#         if self.client_sock:
#             try:
#                 if isinstance(message, dict):
#                     message = json.dumps(message)

#                 self.client_sock.send(message + "\n")
#                 GVL().logger.info(f"Sent to Android: {message}")
#             except bluetooth.BluetoothError as e:
#                 GVL().logger.error(f"Failed to send message: {e}")

#     def receive(self) -> str:
#         """Receives a message from the connected Bluetooth client."""
#         if self.client_sock:
#             try:
#                 data = self.client_sock.recv(1024).decode().strip()
#                 if data:
#                     GVL().logger.info(f"Received from Android: {data}")
#                     return data
#             except bluetooth.BluetoothError as e:
#                 GVL().logger.error(f"Failed to receive message: {e}")
#         return ""

#     def close(self) -> None:
#         """Closes the Bluetooth sockets properly."""
#         if self.client_sock:
#             self.client_sock.close()
#             GVL().logger.info("Closed client socket")

#         if self.server_sock:
#             self.server_sock.close()
#             GVL().logger.info("Closed server socket")

#     def run_until_death(self, callback: Callable[[str], None] = None):
#         """Continuously polls for new data and calls the callback function."""
#         while True:
#             message = self.receive()
#             if message:
#                 print(f"Received: {message}")
#                 if callback:
#                     callback(message)

#     def consume(self, message: dict):
#         """Processes incoming messages and updates GVL state accordingly."""
#         GVL().logger.debug(f"Android Broker received: {message}")
#         if message.get("type") == "algo-data":
#             GVL().android_has_sent_map = True
#             GVL().android_map = message["data"]
#         elif message.get("type") == "command":
#             GVL().taskId = int(message["data"]["taskId"])
#             GVL().start = message["data"]["instruction"] == "start"

#     def cleanup(self):
#         """Cleans up Bluetooth sockets before retrying."""
#         if self.client_sock:
#             self.client_sock.close()
#             self.client_sock = None
#         if self.server_sock:
#             self.server_sock.close()
#             self.server_sock = None

#     def restart_bluetooth(self):
#         """Restarts Bluetooth synchronously and ensures it's discoverable."""
#         GVL().logger.warning("Restarting Bluetooth and making it discoverable...")

#         # Kill any processes using rfcomm
#         os.system("sudo pkill -f rfcomm")
        
#         # Restart Bluetooth service
#         os.system("sudo systemctl restart bluetooth")
#         time.sleep(2)

#         # Ensure Bluetooth adapter is up
#         os.system("sudo hciconfig hci0 up")
#         os.system("sudo hciconfig hci0 piscan")

#         # Optional: Use bluetoothctl as a fallback
#         os.system('echo -e "power on\ndiscoverable on\npairable on\nexit" | sudo bluetoothctl')

#         time.sleep(5)  # ⏳ Wait for Bluetooth to fully restart
#         GVL().logger.warning("Bluetooth restart completed.")



#         # Make Bluetooth discoverable again


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
        self.uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee"  # Unique service UUID

    def setup_server(self):
        """Sets up the Bluetooth server socket and makes it discoverable."""
        GVL().logger.info("Setting up Bluetooth server...")
        self.server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        self.server_sock.bind(("", bluetooth.PORT_ANY))
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
                    self.restart_bluetooth()  # Only restart Bluetooth on the first attempt
                    self.setup_server()  # Start the Bluetooth server

                self.client_sock, self.client_info = self.server_sock.accept()
                GVL().logger.info(f"Accepted connection from {self.client_info}")
                print(f"Accepted connection from {self.client_info}")

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
                print(f"Received: {message}")
                if callback:
                    callback(message)

    def consume(self, message: dict):
        """Processes incoming messages and updates GVL state accordingly."""
        GVL().logger.debug(f"Android Broker received: {message}")
        if message.get("type") == "algo-data":
            GVL().android_has_sent_map = True
            GVL().android_map = message["data"]
            response_instr = GVL().algo_broker.client.send_message(json.dumps(message))
            
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

if __name__ == "__main__":
    android = AndroidBroker()
    res = android.connect()
    if res:
        while True:
            data = android.receive()
            print(data)