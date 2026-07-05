from .memory import ChatbotMemory

import abc as _abc

import ai.chatbot_data as _ai_chatbot_data
import ai.discussion as _ai_discussion

import interactions as _interactions

class ChatbotMemoryFactory[preparation_type]():
    @_abc.abstractmethod
    def get_memory(self, name: str, description: str, discussion: _ai_discussion.ChatbotDiscussion, specs: _ai_chatbot_data.ChatbotSpecs, state: _interactions.CreatorsState) -> ChatbotMemory[preparation_type]:
        ...
        

