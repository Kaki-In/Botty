from .memory_registry import ChatbotMemoryRegistry

import abc as _abc
import ai.discussion as _ai_discussion

class ChatbotMemoryEvaluator(_abc.ABC):
    @_abc.abstractmethod
    def is_relevant(self, memory_name: str, discussion: _ai_discussion.ChatbotDiscussion, query: str, remembering: ChatbotMemoryRegistry.Remembering) -> bool:
        ...

