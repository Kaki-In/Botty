import abc as _abc
import ai.discussion as _ai_discussion
import ai.chatbot_data as _ai_chatbot_data

from ..base import ChatbotMemory
from ..memories import ChatbotDirectoryMemory

import typing as _T

class ChatbotAlwaysTrueMemoryEvaluator(ChatbotDirectoryMemory.Evaluator, _abc.ABC):
    def is_relevant(self, preparation: _T.Any, memory_name: str, remembering: ChatbotMemory.Remembering, discussion: _ai_discussion.ChatbotDiscussion, specs: _ai_chatbot_data.ChatbotSpecs) -> bool:
        return True

