from threading import Thread, Semaphore
import json
import time
from AndroidBroker import AndroidBroker
from ImageBroker import ImageBroker, ImageBrokerRunner
from STMBroker import STMBroker
from SerialBluetooth import SerialBluetooth
from TCPClient import TCPClient
from Broker import Broker
from config import *
import queue
from multiprocessing import Process
from CommandParser import CommandParser
from GlobalVariableManager import GVL

class BrokerCenter:
    def __init__(self):
        self.android_broker: AndroidBroker =  AndroidBroker(strategy=SerialBluetooth(com_port=BLUETOOTH_PORT)),
        self.stm_broker: STMBroker =  STMBroker(com_port=STM_PORT, baud_rate=STM_BAUD_RATE)
        # client brokers
        self.stream: ImageBrokerRunner = ImageBrokerRunner(udp_port=UDP_PORT, ip_address=UDP_IP)
        self.algo_broker: TCPClient = TCPClient(server_host=ALGO_SERVER_HOST, server_port=ALGO_SERVER_PORT)
        self.image_prediction_broker: TCPClient = TCPClient(server_host=ALGO_SERVER_HOST, server_port=ALGO_SERVER_PORT)
        self.running_threads: list[Thread] = []
        self.queue = queue.Queue(maxsize=100)
        self.write_semaphore: Semaphore = Semaphore(1)
        self.read_semaphore: Semaphore = Semaphore(1)
        self._initialise_GVL()
        self.broker_mapper: dict = {
            "stm": self.stm_broker,
            "android": self.android_broker
        }

    def _initialise_GVL(self):
        GVL.initialise({
            "stm_ack": False,
            "algo_ack": False,
            "android_map_data": {} ,
            "android_has_sent_map": False,
            "stm_instruction_list": [],
            "start": False,
            "taskId": -1,
            
        })

    def connect_all(self):
        """Connects all brokers."""
        for broker in self.brokers.values():
            broker.connect()
        # self.stream.connect()

    def add_to_queue(self, message: str):
        """Thread-safe message queuing."""
        self.write_semaphore.acquire()
        # critical section..
        self.queue.put(message)
        # critical section end.
        self.write_semaphore.release()

    def queue_listener(self):
        """Continuously process messages from the shared queue."""
        while True:
            message = self.queue.get()
            # use read semaphore to prevent race conditions

            self.read_semaphore.acquire()
            # critical section..
            print(f"Processed Message: {message}")  # Replace with actual processing logic
            
            try:
                sender, content = CommandParser.json_decode(message)
                # json_dict = json.loads(message)
                # broker_name = json_dict["from"]
                broker: Broker = self.broker_mapper[sender]
                broker.consume(content)
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Invalid message format: {e}")
            finally:
                # ALWAYS RELEASE THE SEMAPHORE AFTER USE
                self.read_semaphore.release()
                self.queue.task_done()

    def start_threads(self):
        """Starts all brokers and listeners as threads."""
        # Start queue listener in a separate thread
        queue_thread = Thread(target=self.queue_listener, daemon=True)
        self.running_threads.append(queue_thread)
        queue_thread.start()

        # Start (Android, STM) brokers as threads
        for broker in [self.android_broker, self.stm_broker]:
            broker_thread = Thread(target=broker.run_until_death, args=(self.add_to_queue,))
            self.running_threads.append(broker_thread)
            broker_thread.start()

        # Start image streaming (previously a Process, now a Thread)
        stream_process = Process(target=self.stream.run_broker_in_process)
        stream_process.start()

        for t in self.running_threads:
            t.join()
        stream_process.join()

    def task1(self):
        # event loop

        # 1. get map data from android

        # 2. send map data to algo server, once received, place paths in path array

        # 3. wait for start signal from android

        # 4. once started, determine which task

        # 5. RPI to determine which task,

        # 6.1. case where its task 1, line by line send queue data to STM, watching out for stops, have a internal coordinates tracker and add to it, to update the android. done go to 7, watch for STOP command
        # 6.2. case where its task 2, custom logic yet to be defined

        # 7. send a path_done signal to android.
        gvl = GVL()
        proc = 0
        temp_buffer = []
        while True:
            if proc == 0:
                if gvl.has_sent_map and gvl.android_map:
                    # reset this flag
                    gvl.has_sent_map = False
                    proc = 10
                    print("Sending map data to algo server")

            if proc == 10:
                response = "error"
                retry = 0
                response = self.algo_broker.send_message(json.dumps(gvl.android_map))
                print(f"Algo response: {response}")
                while response == "error" and retry < 3:
                    print("Algo server error, retrying...")
                    retry += 1
                    time.sleep(5)
                else:
                    # success! parse the response
                    sender, content = CommandParser.parse_command(response)
                    data = content["data"]
                    # parse to STM format
                    gvl.stm_instruction_list = CommandParser.parse_algo_path_to_stm_queue(data)
                    print(f"Parsed instruction list:")
                    proc = 20

            if proc == 20:
                # wait for start
                if gvl.start:
                    # go to 30
                    temp_buffer = gvl.stm_instruction_list
                    gvl.start = False
                    proc = 30

            if proc == 30:
                while len(temp_buffer) > 0:
                    instruction = temp_buffer.pop(0)
                    # look if the instruction is a P command
                    if instruction[0] == "P":
                        # stop and do prediction
                        response = self.image_prediction_broker.send_message("predict")
                        # do something with the response.. idk yet
                    else:
                        # if not prediction, send to stm and wait for ack
                        print(f"Sending instruction: {instruction}")
                        self.stm_broker.send(instruction)
                        while gvl.stm_ack == False:
                            time.sleep(0.1) # wait for ack
                        gvl.stm_ack = False
                # all done! send the path_done signal to android
                proc = 40
            
            if proc == 40:
                # send path_done signal to android
                self.android_broker.send_finished()
                break


    def run(self):
        """Runs the broker center."""
        self.connect_all()
        self.start_threads()

        # Keep the main thread running
        try:
            for thread in self.running_threads:
                thread.join()
        except KeyboardInterrupt:
            print("Stopping all brokers...")

if __name__ == "__main__":
    broker_center = BrokerCenter()
    broker_center.run()
