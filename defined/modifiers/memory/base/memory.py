import abc as _abc
import typing as _T
import ai.discussion as _ai_discussion

from .memory_registry import ChatbotMemoryRegistry
from .memory_evaluator import ChatbotMemoryEvaluator

class ChatbotMemory(_abc.ABC):
    def __init__(self, name: str, evaluator: ChatbotMemoryEvaluator, registry: ChatbotMemoryRegistry) -> None:
        super().__init__()
        
        self.__name = name
        self.__evaluator = evaluator
        self.__registry = registry
        
    @property
    def name(self) -> str:
        return self.__name
    
    @property
    def registry(self) -> ChatbotMemoryRegistry:
        return self.__registry
    
    @property
    def evaluator(self) -> ChatbotMemoryEvaluator:
        return self.__evaluator
    
    def remember_from(self, query: str, for_discussion: _ai_discussion.ChatbotDiscussion) -> _T.Sequence[ChatbotMemoryRegistry.Remembering]:
        relevant_rememberings: list[ChatbotMemoryRegistry.Remembering] = []
        
        for remembering in self.__registry.get_all_rememberings()[:] :
            if self.evaluator.is_relevant(self.__name, for_discussion, query, remembering):
                relevant_rememberings.append(remembering)
            
        return relevant_rememberings
    


