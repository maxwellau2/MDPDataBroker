import json
import math

from GlobalVariableManager import GVL

class CommandParser:
    def __init__(self):
        pass

        

    @staticmethod
    def json_decode(msg: str) -> dict:
        try:
            res = json.loads(msg)
            return res
        except json.decoder.JSONDecodeError:
            # print("Error with decoding, please format data properly")
            return {"error": True}

    @staticmethod
    def parse_command(msg: str):
        # decode
        GVL().logger.debug("")
        content: dict = CommandParser.json_decode(msg)
        # check from who
        sender = content['from']
        return sender, content
                


    @staticmethod
    def map_algo_to_stm_command(algo_command: dict):
        length = 5  # Ensure total length is 5 characters
        movement = ""
        key = list(algo_command.keys())[0]
        leftR = 26
        rightR = 25
        val = algo_command[key]
        if key == "b":
            movement = "BW"
        elif key == "p":
            return "P0100"  # Already 5 characters
        elif key == "s":
            movement = "FW"
        elif key == "l":
            movement = "AF"
            val = int(val/leftR * 180/math.pi)
        elif key == "r":
            movement = "CF"
            val = int(val/rightR * 180/math.pi)
        else:
            return None  # Unhandled movement type

        # Extract and format the numeric part
        numeric_value = int(float(val))  # Convert to int
        numeric_str = str(abs(numeric_value)).zfill(length - len(movement))  # Pad with zeros

        return f"{movement}{numeric_str}"



    @staticmethod
    def parse_algo_path_to_stm_queue(path_list):
        # parse
        parsed_commands = []
        for path in path_list:
            parsed_commands.append(CommandParser.map_algo_to_stm_command(path))
        return parsed_commands
