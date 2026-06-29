import interactions as _interactions
import saves as _saves

from .directory_based_memory import ChatbotDirectoryBasedMemory
from .vectors_based_memory import ChatbotVectorBasedMemory

class ChatbotVectorDirectoryBasedMemory(ChatbotVectorBasedMemory, ChatbotDirectoryBasedMemory):
    def __init__(self, name: str, directory: _saves.ResourcesDirectory, state: _interactions.CreatorsState, embedder_factory: _interactions.CreatorFactory[str, _interactions.EmbeddingVector]) -> None:
        ChatbotVectorBasedMemory.__init__(self, name, directory, state, embedder_factory)
        ChatbotDirectoryBasedMemory.__init__(self, name, directory.get_directory("rememberings"))

    


