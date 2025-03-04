import os
from threading import Thread, Semaphore
import json
import time
import asyncio
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
from GlobalVariableManager import GVL, GVLMonitorRunner
from gvl_websocket import WebSocketGVLMonitor
from Logger import createLogger

if "DISPLAY" not in os.environ or os.environ["DISPLAY"] == "":
    os.environ["DISPLAY"] = ":1"  # Change if needed

class BrokerCenter:
    def __init__(self):
        self.stream: ImageBrokerRunner = ImageBrokerRunner(udp_port=UDP_PORT, ip_address=UDP_IP)
        self.android_broker: AndroidBroker =  AndroidBroker()
        self.stm_broker: STMBroker =  STMBroker(com_port=STM_PORT, baud_rate=STM_BAUD_RATE)
        # client brokers
        # self.algo_broker: TCPClient = TCPClient(server_host=ALGO_TCP_IP, server_port=ALGO_TCP_PORT)
        # maxwell debugging his bullshit lol
        self.algo_broker: TCPClient = TCPClient(server_host=ALGO_TCP_IP, server_port=ALGO_TCP_PORT)
        self.image_prediction_broker: TCPClient = TCPClient(server_host=IMG_TCP_IP, server_port=IMG_TCP_PORT)

        # WebSocket monitor
        self.websocket_monitor = WebSocketGVLMonitor(host= SELF_STATIC_IP, port=WS_PORT)

        self.running_threads: list[Thread] = []
        self.queue: queue.Queue[str] = queue.Queue(maxsize=100)
        self.write_semaphore: Semaphore = Semaphore(1)
        self.read_semaphore: Semaphore = Semaphore(1)
        self.broker_mapper: dict = {
            "stm": self.stm_broker,
            "android": self.android_broker,
            "algo": self.algo_broker,
            "image": self.image_prediction_broker,
        }

    def _initialise_GVL(self):
        GVL.initialise({
            "stm_ack": False,
            "algo_ack": False,
            "android_map_data": {} ,
            "android_has_sent_map": False,
            "stm_instruction_list": [],
            "parsed_stm_instruction_list": [],
            "obstacleIdSequence":[],
            "coordinates":[],
            "start": False,
            "taskId": -1,
            "isRunning": False,
            "logger": createLogger(),
            "algo_broker": self.algo_broker,
            "image_prediction_broker":self.image_prediction_broker,
            "predicted_image": None
        })

    def connect_all(self):
        """Connects all brokers."""
        GVL().logger.info("Connecting..")
        for broker in [self.android_broker,self.stm_broker,self.algo_broker,self.image_prediction_broker]:
            broker.connect()
        GVL().logger.info("Connected..")
        # self.stream.connect()

    def add_to_queue(self, message: str):
        """Thread-safe message queuing."""
        # print(f"queuing {message}")
        self.read_semaphore.acquire()
        # critical section..
        self.queue.put(message)
        # critical section end.
        self.read_semaphore.release()

    def queue_listener(self):
        """Continuously process messages from the shared queue."""
        while True:
            message = self.queue.get()

            if message == '''{"from":"android","msg":{"type":"heartbeat"}}''':
                continue
            # use read semaphore to prevent race conditions

            self.read_semaphore.acquire()
            # critical section..
            # print(f"Processed Message: {message}")  # Replace with actual processing logic
            
            GVL().logger.info(f"Processing Message: {message}")
            try:
                res = CommandParser.json_decode(message.strip())
                if res != "" and res is not None:
                    # json_dict = json.loads(message)
                    # broker_name = json_dict["from"]
                    # print(res)
                    sender = res['from']
                    content = res['msg']
                    # print(sender, content)
                    broker: Broker = self.broker_mapper[sender]
                    broker.consume(content)

                    # check when to run tasks
                    if GVL().start and GVL().taskId == 1 and not GVL().isRunning:
                        GVL().isRunning = True
                        Thread(target=self.task1).start()

            except (json.JSONDecodeError, KeyError) as e:
                GVL().logger.warning(f"Invalid message format: {e}")
            finally:
                # ALWAYS RELEASE THE SEMAPHORE AFTER USE
                # GVL().logger.debug(f"Updated States: {GVL()._shared_borg_state}")
                self.read_semaphore.release()
                self.queue.task_done()

    def start_threads(self):
        """Starts all brokers and listeners as threads."""
        # Start queue listener in a separate thread
        queue_thread = Thread(target=self.queue_listener, daemon=True)
        self.running_threads.append(queue_thread)
        queue_thread.start()

        # # Start WebSocket monitor in a thread
        # def run_websocket_monitor():
        #     asyncio.run(self.websocket_monitor.run())
        tk = Thread(target=GVLMonitorRunner, daemon=True)

        # Start (Android, STM) brokers as threads
        # for broker in [self.stm_broker, self.android_broker, self.image_prediction_broker]:
        for broker in [self.stm_broker, self.android_broker, self.algo_broker, self.image_prediction_broker]:
        # for broker in [self.android_broker, self.stm_broker]:
            broker_thread = Thread(target=broker.run_until_death, args=(self.add_to_queue,))
            self.running_threads.append(broker_thread)
            broker_thread.start()
        
        tk.start()

        # Start image streaming as process
        stream_process = Process(target=self.stream.run_broker_in_process)
        stream_process.start()

        tk.join()
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
        gvl.logger.warning("Starting Task 1")
        proc = 0 # to store the state machine
        temp_buffer = [] # temp buffer to send the instruciton list, using a deep copy
        coordinates_buffer = []
        obstacle_id_buffer = []
        coordinates_idx = 0
        obstacle_idx = 0
        x=0
        y=0
        instruction = "" # variable to store instruction like FW010 or BW010 etc...
        while True:
            
            # 0. Check that map not empty and the map has been sent
            if proc == 0:
                # gvl.logger.info("Task 1 in state 0")
                gvl.logger.debug(f"gvl.android_has_sent_map: {gvl.android_has_sent_map}")
                gvl.logger.debug(f"gvl.android_map_data: {gvl.android_map_data}")
                gvl.logger.debug(f"gvl.stm_instruction_list: {gvl.stm_instruction_list}")
                if gvl.android_has_sent_map and gvl.android_map_data and gvl.stm_instruction_list:
                    # reset this flag
                    gvl.android_has_sent_map = False
                    gvl.parsed_stm_instruction_list = CommandParser.parse_algo_path_to_stm_queue(gvl.stm_instruction_list)
                    proc = 20
                    print("Sending map data to algo server")
                    # self.algo_broker

            # DEPRECATED: we used asynchornous passing of message to reduce overhead
            # 0 skips to 20
            if proc == 10:
                # gvl.logger.info("Task 1 in state 10")
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
                    # gvl.stm_instruction_list = CommandParser.parse_algo_path_to_stm_queue(data)
                    print(f"Parsed instruction list:")
                    proc = 20

            if proc == 20:
                # gvl.logger.info("Task 1 in state 20")
                # wait for start
                if gvl.start:
                    # go to 30
                    temp_buffer = gvl.parsed_stm_instruction_list
                    coordinates_buffer = gvl.coordinates
                    obstacle_id_buffer = gvl.obstacleIdSequence
                    gvl.start = False
                    proc = 30

            if proc == 30:
                # gvl.logger.info("Task 1 in state 30")
                # retrive instruction
                instruction = None
                stop = False
                if len(temp_buffer) > 0:
                    instruction = temp_buffer.pop(0)
                    print(instruction, type(instruction))
                else:
                    stop = True
                if instruction is not None:
                    coord = coordinates_buffer[coordinates_idx]
                    x,y = coord
                    x,y = x/10,y/10
                    if instruction[0] != 'P':
                        self.android_broker.send_moving(x,y,'N')
                        coordinates_idx += 1
                    else:
                        self.android_broker.send_scanning(x,y,'N')
                    proc = 31
                elif stop == False:
                    proc = 30 # take again
                else:
                    proc = 40

            if proc == 31:
                # gvl.logger.info("Task 1 in state 31")
                # process instruction
                if instruction[0] == "P":
                    # stop and do prediction
                    gvl.predicted_image = None
                    GVL().logger.info(f"Scanning Image")
                    self.image_prediction_broker.send("predict")
                    while(not gvl.predicted_image):
                        time.sleep(0.1)
                    GVL().logger.info(f"Predicted image: {gvl.predicted_image}")
                    obstacle_id = obstacle_id_buffer[obstacle_idx]
                    self.android_broker.send_obstacle_image_found(x,y,'N',obstacle_id,21)
                    obstacle_idx += 1
                    time.sleep(2)
                    # do something with the response.. idk yet
                else:
                    # if not prediction, send to stm and wait for ack
                    gvl.logger.info(f"Sending instruction: {instruction}")
                    gvl.logger.info(instruction)
                    self.stm_broker.send(instruction)
                    # break
                # go and wait for the ack in 32
                proc = 32 if not instruction[0] == "P" else 30

            if proc == 32:
                # gvl.logger.info("Task 1 in state 32")
                # wait for acknowledgement
                if gvl.stm_ack == True:
                    gvl.stm_ack = False
                    proc = 30
            
            if proc == 40:
                # gvl.logger.info("Task 1 in state 40")
                # send path_done signal to android
                # self.android_broker.send_finished()
                GVL().isRunning=False
                gvl.logger.info("Finishing up")
                last_coord = coordinates_buffer[-1]
                x,y = last_coord[0]/10, last_coord[1]/10
                self.android_broker.send_idling(x,y,'N')
                self.android_broker.send_finished(x,y,'N')
                break


    def run(self):
        """
        Run the broker center
        """
        self.connect_all()
        self._initialise_GVL()
        self.start_threads()
        # Start all brokers
        # for broker in self.broker_mapper.values():
        #     broker_thread = Thread(target=broker.run)
        #     self.running_threads.append(broker_thread)
        #     broker_thread.start()

        

        # Tkinter Monitor Thread (uncomment to use Tkinter)
        monitor_thread = Thread(target=self.gvl_monitor.run_GVL_monitor)
        monitor_thread.start()
        self.running_threads.append(monitor_thread)

        # # Start image streaming as process
        # stream_process = Process(target=self.stream.run_broker_in_process)
        # stream_process.start()

        # Keep the main thread running
        # try:
        #     for thread in self.running_threads:
        #         thread.join()
        # except KeyboardInterrupt:
        #     print("Stopping all brokers...")

if __name__ == "__main__":
    broker_center = BrokerCenter()
    broker_center.run()
