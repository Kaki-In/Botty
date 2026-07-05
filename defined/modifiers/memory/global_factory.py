from .base import ChatbotMemory, ChatbotMemoryFactory
from .memories import ChatbotDirectoryMemory

import ai.chatbot_data as _ai_chatbot_data
import ai.discussion as _ai_discussion

import interactions as _interactions

class GlobalChatbotMemoryFactory[preparation_type](ChatbotMemoryFactory[preparation_type]):
    def __init__(self, evaluator: ChatbotDirectoryMemory.Evaluator[preparation_type]) -> None:
        super().__init__()
        
        self.__evaluator = evaluator
        
    @property
    def evaluator(self) -> ChatbotDirectoryMemory.Evaluator[preparation_type]:
        return self.__evaluator
    
    def get_memory(self, name: str, description: str, discussion: _ai_discussion.ChatbotDiscussion, specs: _ai_chatbot_data.ChatbotSpecs, state: _interactions.CreatorsState) -> ChatbotMemory[preparation_type]:
        return ChatbotDirectoryMemory(name, description, self.__evaluator, specs.configuration_directory.get_directory('memory:'+name))

