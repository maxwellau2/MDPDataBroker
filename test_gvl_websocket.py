#!/usr/bin/env python3
import asyncio
import websockets
import json
import random
import time

async def simulate_gvl_updates(websocket):
    """Simulate GVL updates with random data."""
    print("New client connected!")
    
    # Initial state
    state = {
        "stm_ack": False,
        "algo_ack": True,
        "android_map_data": {
            "robot": {
                "x": 0,
                "y": 0,
                "direction": "N"
            },
            "obstacles": [
                {"id": 1, "x": 10, "y": 20, "direction": "N"},
                {"id": 2, "x": 30, "y": 40, "direction": "S"}
            ]
        },
        "android_has_sent_map": False,
        "stm_instruction_list": ["FORWARD", "LEFT", "RIGHT"],
        "start": False,
        "taskId": 1,
        "isRunning": True,
        "obstacleIdSequence": [1, 2, 3, 4, 5]
    }
    
    # Send initial state
    await websocket.send(json.dumps({"type": "initial_state", "data": state}))
    print("Sent initial state!")
    
    try:
        while True:
            # Simulate random changes
            state["stm_ack"] = random.choice([True, False])
            state["android_map_data"]["robot"] = {
                "x": random.randint(0, 100),
                "y": random.randint(0, 100),
                "direction": random.choice(["N", "S", "E", "W"])
            }
            state["android_map_data"]["obstacles"] = [
                {
                    "id": i,
                    "x": random.randint(0, 100),
                    "y": random.randint(0, 100),
                    "direction": random.choice(["N", "S", "E", "W"])
                }
                for i in range(1, 3)
            ]
            state["start"] = random.choice([True, False])
            state["taskId"] = random.randint(1, 5)
            
            # Send update
            message = json.dumps({"type": "state_update", "data": state})
            await websocket.send(message)
            print(f"Sent update: {message}")
            await asyncio.sleep(2)  # Update every 2 seconds
            
    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected!")

async def main():
    print("Starting test WebSocket server...")
    server = await websockets.serve(simulate_gvl_updates, "localhost", 8766)
    print("WebSocket server is running at ws://localhost:8766")
    print("Open gvl_monitor.html in your web browser to see the updates!")
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
