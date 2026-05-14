from .creator_factory import CreatorFactory
from .creator import Creator
from .creators_state import CreatorsState

import typing as _T
import typing_extensions as _TE
import saves as _saves
import asyncio as _asyncio

class CreatorsMap():
    def __init__(self) -> None:
        self.__creators: dict[tuple[_T.Type, _T.Type], CreatorFactory] = {}
        self.__current_creator: _T.Optional[Creator] = None

    @property
    def current_creator(self) -> Creator | None:
        return self.__current_creator
 
    def get_creator_factory[InteractionDescriptorType, InteractionType](self,
                                                                iobjt: _T.Type[InteractionDescriptorType],
                                                                objt: _T.Type[InteractionType]) -> CreatorFactory[InteractionDescriptorType, InteractionType]:
        return self.__creators[iobjt, objt]
    
    @_TE.deprecated("Deprecated, because the creator should be created manually to be interrupted")
    def create[InteractionDescriptorType, InteractionType](self, description: InteractionDescriptorType, source_type: _T.Type[InteractionDescriptorType], required_type: _T.Type[InteractionType], directory: _saves.ResourcesDirectory) -> InteractionType:
        creator_factory = self.get_creator_factory(source_type, required_type)
        return creator_factory.build_from(directory).create_object_from(description)
    
    def create_under_state[InteractionDescriptorType, InteractionType](self, state: CreatorsState, description: InteractionDescriptorType, source_type: _T.Type[InteractionDescriptorType], required_type: _T.Type[InteractionType], directory: _saves.ResourcesDirectory) -> InteractionType:
        creator_factory = self.get_creator_factory(source_type, required_type)
        return state.create_from_factory(creator_factory, description, directory)
    
    async def async_create_under_state[InteractionDescriptorType, InteractionType](self, state: CreatorsState, description: InteractionDescriptorType, source_type: _T.Type[InteractionDescriptorType], required_type: _T.Type[InteractionType], directory: _saves.ResourcesDirectory) -> InteractionType:
        return await _asyncio.get_event_loop().run_in_executor(None, lambda:self.create_under_state(state, description, source_type, required_type, directory))
    
    def add_creator_factory[InteractionDescriptorType, InteractionType](self, creator: CreatorFactory[InteractionDescriptorType, InteractionType],
                                                                iobjt: _T.Type[InteractionDescriptorType],
                                                                objt: _T.Type[InteractionType]) -> None:
        self.__creators[iobjt, objt] = creator

