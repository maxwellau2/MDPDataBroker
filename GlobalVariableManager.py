from typing import cast
from typing_extensions import TypedDict 
import logging

from Logger import createLogger

class GVLState(TypedDict):
    stm_ack: bool
    algo_ack: bool
    android_map_data: dict 
    android_has_sent_map: bool
    stm_instruction_list: list
    start: bool
    taskId: int
    isRunning: bool
    obstacleIdSequence:list
    logger: logging.Logger

class GVL:
    _shared_borg_state: GVLState = cast(GVLState,{
            "stm_ack": False,
            "algo_ack": False,
            "android_map_data": {} ,
            "android_has_sent_map": False,
            "stm_instruction_list": [],
            "start": False,
            "taskId": -1,
            "isRunning": False,
            "obstacleIdSequence":[],
            "logger": createLogger(),
        })  # Shared state across all instances
    _callbacks = []  # List of functions to call on update

    def __new__(cls, *args, **kwargs):
        obj = super(GVL, cls).__new__(cls, *args, **kwargs)
        obj.__dict__ = cls._shared_borg_state
        return obj
    
    @staticmethod
    def initialise(dic: dict):
        """Initialize GVL state."""
        GVL._shared_borg_state = dic

    def __setattr__(self, key, value):
        """Detects changes in GVL and triggers callbacks, but prevents infinite recursion."""
        if key in self._shared_borg_state and self._shared_borg_state[key] == value:
            return  # No actual change, avoid triggering callbacks

        # Update the shared state
        self._shared_borg_state[key] = value

        # Trigger registered callbacks
        for callback in GVL._callbacks:
            try:
                callback()
            except RecursionError:
                print(f"Warning: Skipping recursive callback for {key}")

    def __getattr__(self, key):
        """Retrieve attributes from the shared GVL state."""
        if key in self._shared_borg_state:
            return self._shared_borg_state[key]
        raise AttributeError(f"'GVL' object has no attribute '{key}'")

    @staticmethod
    def register_callback(callback):
        """Allows external functions (e.g., GUI updates) to register for state changes."""
        GVL._callbacks.append(callback)




import tkinter as tk
from tkinter import ttk
from GlobalVariableManager import GVL

class GVLMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("GVL Monitor")
        self.root.geometry("500x400")

        # Create frame and table
        self.frame = ttk.Frame(root)
        self.frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.tree = ttk.Treeview(self.frame, columns=("Variable", "Value"), show="headings")
        self.tree.heading("Variable", text="Variable")
        self.tree.heading("Value", text="Value")
        self.tree.column("Variable", width=150)
        self.tree.column("Value", width=300)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Register update callback safely
        GVL.register_callback(self.safe_update_values)
        self.update_values()  # Initial load

    def safe_update_values(self):
        """Safe wrapper to avoid recursion issues in Tkinter."""
        self.root.after(100, self.update_values)  # Schedule update in Tkinter's event loop

    def update_values(self):
        """Updates the UI when GVL changes"""
        gvl = GVL()._shared_borg_state

        # Clear old values
        for row in self.tree.get_children():
            self.tree.delete(row)

        # Insert updated values
        for key, value in gvl.items():
            self.tree.insert("", "end", values=(key, str(value)))


class GVLMonitorRunner:
    def __init__(self):
        pass
    
    @staticmethod
    def run_GVL_monitor():
        root = tk.Tk()
        app = GVLMonitor(root)
        root.mainloop()
