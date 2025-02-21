from AndroidBroker import AndroidBroker
import platform
from SerialBluetooth import SerialBluetooth
from STMBroker import STMBroker
from config import *

if __name__ == "__main__":
    bluetooth_strategy = SerialBluetooth(com_port="/dev/rfcomm0")  # Replace with correct COM port
    broker = AndroidBroker(strategy=bluetooth_strategy)

    stm = STMBroker(STM_PORT, STM_BAUD_RATE)
    
    if broker.connect() == 1 and stm.connect() == 1:
        try:
            while True:
                message = broker.receive()
                # print("Hello")
                if message is not None and message != "":
                    # print(f"Received: {message}")
                    # broker.send(f"Echo: {message}")
                    stm.send(message)
                    # broker.send("ur mam gay")

        except KeyboardInterrupt:
            print("Stopping Bluetooth server...")
        finally:
            broker.close()
