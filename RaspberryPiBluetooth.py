from BluetoothStrategy import BluetoothStrategy
import platform

# trying import, important for dev vs prod
if platform.system() != "Linux":
    raise RuntimeError(f"This is only for Linux (RPI), you are on {platform.system()}")
import bluetooth
class RaspberryPiBluetooth(BluetoothStrategy):
    def __init__(self, uuid="00001101-0000-1000-8000-00805f9b34fb"):
        self.uuid = uuid
        self.server_socket = None
        self.client_socket = None
        self.client_address = None

    def connect(self) -> int:
        try:
            self.server_socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            self.server_socket.bind(("", bluetooth.PORT_ANY))
            self.server_socket.listen(1)

            bluetooth.advertise_service(
                self.server_socket,
                "AndroidBroker",
                service_id=self.uuid,
                service_classes=[self.uuid, bluetooth.SERIAL_PORT_CLASS],
                profiles=[bluetooth.SERIAL_PORT_PROFILE]
            )

            print("Waiting for Bluetooth connection...")
            self.client_socket, self.client_address = self.server_socket.accept()
            print(f"Connected to {self.client_address}")
            return 1  # Success
        except Exception as e:
            print(f"Bluetooth connection failed: {e}")
            return -1  # Error

    def send(self, message: str) -> None:
        if self.client_socket:
            self.client_socket.send(message.encode())
            print(f"Sent: {message}")

    def receive(self) -> str:
        if self.client_socket:
            data = self.client_socket.recv(1024).decode("utf-8")
            print(f"Received: {data}")
            return data
        return ""

    def close(self) -> None:
        if self.client_socket:
            self.client_socket.close()
        if self.server_socket:
            self.server_socket.close()
        print("Bluetooth connection closed (Raspberry Pi)")