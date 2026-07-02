import abc as _abc
import typing as _T
import ai.discussion as _ai_discussion

from .memory_registry import ChatbotMemoryRegistry
from .memory_evaluator import ChatbotMemoryEvaluator

class ChatbotMemory[mem_registry: ChatbotMemoryRegistry, mem_evaluator: ChatbotMemoryEvaluator](_abc.ABC):
    def __init__(self, name: str, evaluator: mem_evaluator, registry: mem_registry) -> None:
        super().__init__()
        
        self.__name = name
        self.__evaluator = evaluator
        self.__registry = registry
        
    @property
    def name(self) -> str:
        return self.__name
    
    @property
    def registry(self) -> mem_registry:
        return self.__registry
    
    @property
    def evaluator(self) -> mem_evaluator:
        return self.__evaluator
    
    def remember_from(self, query: str, for_discussion: _ai_discussion.ChatbotDiscussion) -> _T.Sequence[ChatbotMemoryRegistry.Remembering]:
        relevant_rememberings: list[ChatbotMemoryRegistry.Remembering] = []
        
        for remembering in self.__registry.get_all_rememberings()[:] :
            if self.evaluator.is_relevant(self.__name, for_discussion, query, remembering):
                relevant_rememberings.append(remembering)
            
        return relevant_rememberings
    


