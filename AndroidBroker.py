from typing import Callable
from Broker import Broker
import platform  # To detect OS
from BluetoothStrategy import BluetoothStrategy
from GlobalVariableManager import GVL
from RaspberryPiBluetooth import RaspberryPiBluetooth

class AndroidBroker(Broker):
    def __init__(self, strategy: BluetoothStrategy):
        self.strategy = strategy

    def connect(self) -> int:
        return self.strategy.connect()

    def send(self, message: str) -> None:
        self.strategy.send(message)

    def receive(self) -> str:
        return self.strategy.receive()

    def close(self) -> None:
        self.strategy.close()

    def run_until_death(self, callback: Callable[[str], None] = None):
        while True:
            message = self.receive()
            if message:
                if callback:
                    callback(message)

    def consume(self, message: dict):
        print(f"Android Broker receieved: {message}")
        if message["type"] == "algo-data":
            GVL().android_has_sent_map = True
            GVL().android_map = message["data"]
            print(f"Android Broker received map data: {message['data']}")
        elif message["type"] == "command":
            GVL().taskId = int(message["data"]["taskId"])
            GVL().start = bool(message["data"]["instruction"] == "start")
        self.send(f"Echo from server: {message}")


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