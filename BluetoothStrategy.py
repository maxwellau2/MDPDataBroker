from abc import ABC, abstractmethod

class BluetoothStrategy(ABC):
    @abstractmethod
    def connect(self) -> int:
        pass

    @abstractmethod
    def send(self, message: str) -> None:
        pass

    @abstractmethod
    def receive(self) -> str:
        pass

    @abstractmethod
    def close(self) -> None:
        pass
