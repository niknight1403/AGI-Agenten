from abc import ABC, abstractmethod
class BaseAgent(ABC):
    name = "base"
    description = ""
    @abstractmethod
    async def process(self, payload):
        raise NotImplementedError
    def describe(self):
        return {"name": self.name, "description": self.description}
