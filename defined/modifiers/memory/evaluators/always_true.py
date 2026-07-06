import abc as _abc
import interactions as _interactions
import typing as _T

import ai.discussion as _ai_discussion
import ai.chatbot_data as _ai_chatbot_data

from ..base import ChatbotMemory
from ..memories import ChatbotDirectoryMemory

class ChatbotAlwaysTrueMemoryEvaluator(ChatbotDirectoryMemory.Evaluator, _abc.ABC):
    def is_relevant(self, state: _interactions.CreatorsState, preparation: _T.Any, memory_name: str, remembering: ChatbotMemory.Remembering, discussion: _ai_discussion.ChatbotDiscussion, specs: _ai_chatbot_data.ChatbotSpecs) -> bool:
        return True

