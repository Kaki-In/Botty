from .base import ChatbotMemory, ChatbotMemoryFactory, ChatbotMemoryEvaluator
from .registers import ChatbotDirectoryMemoryRegistry

import ai.chatbot_data as _ai_chatbot_data
import ai.discussion as _ai_discussion

import interactions as _interactions

class GlobalChatbotMemoryFactory(ChatbotMemoryFactory):
    def __init__(self, evaluator: ChatbotMemoryEvaluator) -> None:
        super().__init__()
        
        self.__evaluator = evaluator
        
    @property
    def evaluator(self) -> ChatbotMemoryEvaluator:
        return self.__evaluator
    
    def get_memory(self, name: str, specs: _ai_chatbot_data.ChatbotSpecs, discussion: _ai_discussion.ChatbotDiscussion, state: _interactions.CreatorsState) -> ChatbotMemory:
        return ChatbotMemory(name, self.__evaluator, ChatbotDirectoryMemoryRegistry(specs.configuration_directory.get_directory('memory:'+name)))

