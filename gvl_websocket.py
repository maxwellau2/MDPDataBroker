import websockets
import asyncio
import json
from GlobalVariableManager import GVL
import logging
import config
from queue import Queue
from threading import Lock

class WebSocketGVLMonitor:
    def __init__(self, host=config.SELF_STATIC_IP, port=config.WS_PORT):
        self.host = host
        self.port = port
        self.connected_clients = set()
        self.logger = logging.getLogger(__name__)
        self.update_queue = Queue()
        self.lock = Lock()
        
    def get_gvl_state(self):
        """Get current GVL state as a JSON-serializable dict."""
        with self.lock:
            state = {}
            gvl = GVL()
            for key, value in gvl.__dict__.items():
                if key != 'logger' and not key.startswith('_'):
                    if isinstance(value, (list, dict)):
                        state[key] = value
                    else:
                        state[key] = str(value)
            return state

    async def notify_state_change(self):
        """Notify all connected clients of state change."""
        if not self.connected_clients:
            return
            
        try:
            message = {
                "type": "state_update",
                "data": self.get_gvl_state()
            }
            websockets.broadcast(self.connected_clients, json.dumps(message))
        except Exception as e:
            self.logger.error(f"Error broadcasting state: {e}")

    async def register(self, websocket):
        """Register a new client."""
        self.connected_clients.add(websocket)
        # Send initial state
        try:
            message = {
                "type": "state_update",
                "data": self.get_gvl_state()
            }
            await websocket.send(json.dumps(message))
        except Exception as e:
            self.logger.error(f"Error sending initial state: {e}")

    async def unregister(self, websocket):
        """Unregister a client."""
        self.connected_clients.remove(websocket)

    def setup_gvl_callback(self):
        """Setup callback for GVL changes."""
        def callback():
            """Non-async callback that just queues the update."""
            self.update_queue.put(True)
            
        GVL.register_callback(callback)

    async def process_updates(self):
        """Process queued updates."""
        while True:
            try:
                # Non-blocking check for updates
                if not self.update_queue.empty():
                    self.update_queue.get()
                    await self.notify_state_change()
                await asyncio.sleep(0.1)  # Small delay to prevent CPU hogging
            except Exception as e:
                self.logger.error(f"Error processing updates: {e}")

    async def ws_handler(self, websocket, path):
        """Handle websocket connections."""
        await self.register(websocket)
        try:
            async for message in websocket:
                # Handle any incoming messages if needed
                pass
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister(websocket)

    async def run(self):
        """Run the websocket server."""
        self.setup_gvl_callback()
        async with websockets.serve(self.ws_handler, self.host, self.port):
            self.logger.info(f"WebSocket server started at ws://{self.host}:{self.port}")
            # Start update processor
            update_task = asyncio.create_task(self.process_updates())
            await update_task

def run_websocket_monitor():
    """Run the websocket monitor."""
    monitor = WebSocketGVLMonitor()
    asyncio.run(monitor.run())

# if __name__ == "__main__":
#     run_websocket_monitor()
