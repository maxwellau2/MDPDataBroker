import asyncio
import websockets
import json
from GlobalVariableManager import GVL
import logging

class WebSocketGVLMonitor:
    def __init__(self, host='0.0.0.0', port=8765):
        self.host = host
        self.port = port
        self.connected_clients = set()
        self.logger = logging.getLogger('WebSocketGVLMonitor')

    def get_gvl_state(self):
        """Get current GVL state as a JSON-serializable dict."""
        state = {}
        for key, value in GVL._shared_borg_state.items():
            if key != 'logger':  # Skip logger object
                # Convert any complex types to strings if needed
                if isinstance(value, (list, dict)):
                    state[key] = json.dumps(value)
                else:
                    state[key] = str(value)
        return state

    async def broadcast_state(self):
        """Broadcast current state to all connected clients."""
        if not self.connected_clients:
            return
        
        state = self.get_gvl_state()
        message = json.dumps({"type": "state_update", "data": state})
        
        # Broadcast to all connected clients
        if self.connected_clients:
            await asyncio.gather(
                *[client.send(message) for client in self.connected_clients],
                return_exceptions=True
            )

    async def register(self, websocket):
        """Register a new client connection."""
        self.connected_clients.add(websocket)
        self.logger.info(f"New client connected. Total clients: {len(self.connected_clients)}")
        
        # Send initial state
        state = self.get_gvl_state()
        await websocket.send(json.dumps({"type": "initial_state", "data": state}))

    async def unregister(self, websocket):
        """Unregister a client connection."""
        self.connected_clients.remove(websocket)
        self.logger.info(f"Client disconnected. Total clients: {len(self.connected_clients)}")

    async def ws_handler(self, websocket, path):
        """Handle WebSocket connections."""
        await self.register(websocket)
        try:
            async for message in websocket:
                # Handle any incoming messages if needed
                pass
        finally:
            await self.unregister(websocket)

    def setup_gvl_callback(self):
        """Setup callback for GVL updates."""
        async def callback():
            await self.broadcast_state()
        
        # Register the callback with GVL
        GVL.register_callback(lambda: asyncio.create_task(callback()))

    async def run(self):
        """Start the WebSocket server."""
        self.setup_gvl_callback()
        async with websockets.serve(self.ws_handler, self.host, self.port):
            self.logger.info(f"WebSocket server started at ws://{self.host}:{self.port}")
            await asyncio.Future()  # run forever

def run_websocket_monitor():
    """Function to run the WebSocket monitor in a separate process."""
    monitor = WebSocketGVLMonitor()
    asyncio.run(monitor.run())

if __name__ == "__main__":
    run_websocket_monitor()
