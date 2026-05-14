import saves as _saves
import abc as _abc

from .creator import Creator

class CreatorFactory[InteractionDescriptorType, InteractionType](_abc.ABC):
    @_abc.abstractmethod
    def build_from(self, directory: _saves.ResourcesDirectory) -> Creator[InteractionDescriptorType, InteractionType]:
        ...


