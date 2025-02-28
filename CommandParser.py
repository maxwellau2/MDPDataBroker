import json

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
        movement = ""
        key = list(algo_command.keys())[0]
        if key == "s" and algo_command[key] < 0:
            movement = "BW"
        elif key == "s":
            movement = "FW"
        elif key == "l":
            movement = "A"
        elif key == "r":
            movement = "C"
        else:
            # print(f"uncaught movement type: {key}")
            return None
        if movement in ['A', 'C']: # add the sapce
            return f"{movement} {int(float(algo_command[key]))}"
        return f"{movement}{int(float(algo_command[key]))}"



    @staticmethod
    def parse_algo_path_to_stm_queue(path_list):
        # parse
        parsed_commands = []
        for path in path_list:
            parsed_commands.append(CommandParser.map_algo_to_stm_command(path))
        return parsed_commands
