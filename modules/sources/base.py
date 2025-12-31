from abc import ABC, abstractmethod
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class Target:
    url: str
    kind: str # RADIO or IMAGE
    object_name: str
    dataset: str
    metadata: Dict[str, Any] = None

class DataSource(ABC):
    """
    Abstract Base Class for Universe Data Sources.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def kind(self) -> str:
        """RADIO or IMAGE"""
        pass
        
    @abstractmethod
    def discover(self) -> List[Target]:
        """
        Returns a list of potential Targets to harvest.
        Should handle its own logic (APIs, scraping, seeds).
        """
        pass
