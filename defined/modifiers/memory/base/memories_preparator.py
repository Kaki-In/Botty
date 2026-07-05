from .memory import ChatbotMemory
from .memory_factory import ChatbotMemoryFactory

import typing as _T
import abc as _abc

import ai.discussion as _ai_discussion
import ai.chatbot_data as _ai_chatbot_data

class ChatbotMemoriesPreparator[preparation_type](_abc.ABC):
    def __init__(self, **memory_factories: tuple[ChatbotMemoryFactory[preparation_type], str]) -> None:
        super().__init__()
        
        self.__memories: dict[str, tuple[ChatbotMemoryFactory[preparation_type], str]] = memory_factories or {}
        
    @property
    def memories(self) -> _T.Mapping[str, tuple[ChatbotMemoryFactory[preparation_type], str]]:
        return self.__memories
    
    def add_memory(self, name: str, memory_factory: ChatbotMemoryFactory[preparation_type], description: str) -> None:
        self.__memories[name] = (memory_factory, description)
        
    def remove_memory(self, name: str) -> None:
        del self.__memories[name]
        
    @property
    def memory_names(self) -> _T.Collection[str]:
        return self.__memories.keys()
    
    def get_memory_factory_by_name(self, name: str) -> ChatbotMemoryFactory[preparation_type]:
        return self.__memories[name][0]
    
    @_abc.abstractmethod
    def _prepare_remembering(self, discussion: _ai_discussion.ChatbotDiscussion, specs: _ai_chatbot_data.ChatbotSpecs) -> preparation_type:
        ...
        
    def get_rememberings_for(self, discussion: _ai_discussion.ChatbotDiscussion, specs: _ai_chatbot_data.ChatbotSpecs) -> _T.Mapping[str, tuple[ChatbotMemory, _T.Sequence[ChatbotMemory.Remembering]]]:
        preparation = self._prepare_remembering(discussion, specs)
        
        rememberings: dict[str, tuple[ChatbotMemory, _T.Sequence[ChatbotMemory.Remembering]]] = {}
        
        for name, (factory, description) in self.__memories.items():
            memory = factory.get_memory(name, description, discussion, specs, discussion.creators_state)
            rememberings[name] = (memory, memory.get_linked_rememberings(preparation, discussion, specs))
        
        return rememberings


