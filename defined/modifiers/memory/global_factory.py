from .base import ChatbotMemoryFactory
from .helpers import ChatbotVectorDirectoryBasedMemory

import ai.chatbot_data as _ai_chatbot_data
import ai.discussion as _ai_discussion

import interactions as _interactions

class GlobalChatbotMemoryFactory(ChatbotMemoryFactory[ChatbotVectorDirectoryBasedMemory]):
    def __init__(self, embedder: _interactions.CreatorFactory[str, _interactions.EmbeddingVector]) -> None:
        super().__init__()
        
        self.__embedder = embedder
        
    @property
    def embedder(self) -> _interactions.CreatorFactory[str, _interactions.EmbeddingVector]:
        return self.__embedder
    
    def get_memory(self, name: str, specs: _ai_chatbot_data.ChatbotSpecs, discussion: _ai_discussion.ChatbotDiscussion, state: _interactions.CreatorsState) -> ChatbotVectorDirectoryBasedMemory:
        return ChatbotVectorDirectoryBasedMemory(name, specs.configuration_directory.get_directory('memory'+name), state, self.__embedder)

