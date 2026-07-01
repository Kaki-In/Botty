from ..base import ChatbotMemoryEvaluator, ChatbotMemoryRegistry

import abc as _abc
import ai.discussion as _ai_discussion

class ChatbotAlwaysTrueMemoryEvaluator(ChatbotMemoryEvaluator, _abc.ABC):
    def is_relevant(self, memory_name: str, discussion: _ai_discussion.ChatbotDiscussion, query: str, remembering: ChatbotMemoryRegistry.Remembering) -> bool:
        return True

