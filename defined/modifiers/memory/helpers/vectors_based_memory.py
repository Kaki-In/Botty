from ..base import ChatbotMemory

import interactions as _interactions
import saves as _saves
import abc as _abc
import typing as _T

class _vector_based_memory_configuration_object(_T.TypedDict):
    threshold: float

class ChatbotVectorBasedMemory(ChatbotMemory, _abc.ABC):
    def __init__(self, name: str, directory: _saves.ResourcesDirectory, state: _interactions.CreatorsState, embedder_factory: _interactions.CreatorFactory[str, _interactions.EmbeddingVector]) -> None:
        super().__init__(name)
        
        self.__directory = directory
        
        self.__state = state
        self.__embedder_factory = embedder_factory
        
        self.__configuration = _saves.ConfigurationFile[_vector_based_memory_configuration_object](self.__directory.get_resource('settings.conf'), {
            'threshold': 0.5
        }).read_configuration()
        
    @property
    def directory(self) -> _saves.ResourcesDirectory:
        return self.__directory
    
    @property
    def creators_state(self) -> _interactions.CreatorsState:
        return self.__state
    
    @property
    def embedder_factory(self) -> _interactions.CreatorFactory[str, _interactions.EmbeddingVector]:
        return self.__embedder_factory
    
    def is_relevant(self, query: str, remembering: ChatbotMemory.Remembering) -> bool:
        embedded_query = self.__state.create_from_factory(self.__embedder_factory, query, self.__directory)
        embedded_document = self.__state.create_from_factory(self.__embedder_factory, str(remembering), self.__directory)
        
        return _interactions.EmbeddingVector.similarity_between(embedded_query, embedded_document) > self.__configuration['threshold']

