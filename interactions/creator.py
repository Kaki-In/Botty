import abc as _abc

from .interruption_error import InteractionInterruptionError

class Creator[InteractionDescriptorType, InteractionType](_abc.ABC):
    def __init__(self):
        self.__should_interrupt = False

    def create_object_from(self, description: InteractionDescriptorType) -> InteractionType:
        try:
            self.raise_interruption_if_needed()
            return self.if_no_interruption(self._create_object_from(description))
        finally:
            self.on_finish()

    @_abc.abstractmethod
    def _create_object_from(self, description: InteractionDescriptorType) -> InteractionType:
        ...

    def on_interruption(self) -> None:
        ...
    
    @property
    def should_interrupt(self) -> bool:
        return self.__should_interrupt
    
    def on_finish(self) -> None:
        ...

    def interrupt(self) -> None:
        print("Interrupting", self)
        self.on_interruption()
        self.__should_interrupt = True
    
    def raise_interruption_if_needed(self) -> None:
        if self.__should_interrupt:
            raise InteractionInterruptionError
    
    def if_no_interruption[value](self, data: value) -> value:
        self.raise_interruption_if_needed()
        return data

