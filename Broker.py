from abc import ABC, abstractmethod
from typing import Callable

class Broker(ABC):
    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def send(self, message):
        pass

    @abstractmethod
    def receive(self):
        pass

    @abstractmethod
    def run_until_death(self, callback: Callable[[str], None]):
        pass

    @abstractmethod
    def consume(self, message: str):
        pass

    