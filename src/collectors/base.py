from abc import ABC, abstractmethod

class BaseCollector(ABC):
    nome: str = "base"
    

    def __init__ (self, config: dict):
        self.config = config

    @abstractmethod
    def coletar(self, termos: list[str]) :
        ...