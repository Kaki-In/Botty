from .memory import ChatbotMemory

import abc as _abc

import ai.chatbot_data as _ai_chatbot_data
import ai.discussion as _ai_discussion

import interactions as _interactions

class ChatbotMemoryFactory[mem: ChatbotMemory]():
    @_abc.abstractmethod
    def get_memory(self, name: str, specs: _ai_chatbot_data.ChatbotSpecs, discussion: _ai_discussion.ChatbotDiscussion, state: _interactions.CreatorsState) -> mem:
        ...
        

