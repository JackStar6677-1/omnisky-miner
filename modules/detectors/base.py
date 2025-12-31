from abc import ABC, abstractmethod

class Detector(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def detect(self, event_data: dict) -> dict:
        """
        Returns {score: 0-100, label: str, metadata: dict}
        """
        pass
