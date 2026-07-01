from ..base import ChatbotMemoryEvaluator, ChatbotMemoryRegistry

import interactions as _interactions
import saves as _saves
import abc as _abc
import typing as _T
import hashlib as _hashlib
import ai.discussion as _ai_discussion

class _vector_based_memory_configuration_object(_T.TypedDict):
    threshold: float

class ChatbotVectorMemoryEvaluator(ChatbotMemoryEvaluator, _abc.ABC):
    def __init__(self, cache_directory: _saves.ResourcesDirectory, embedder_factory: _interactions.CreatorFactory[str, _interactions.EmbeddingVector]) -> None:
        super().__init__()
        
        self.__directory = cache_directory
        
        self.__embedder_factory = embedder_factory
        
    @property
    def directory(self) -> _saves.ResourcesDirectory:
        return self.__directory
    
    @property
    def embedder_factory(self) -> _interactions.CreatorFactory[str, _interactions.EmbeddingVector]:
        return self.__embedder_factory
    
    def get_embedding(self, document: str, discussion: _ai_discussion.ChatbotDiscussion) -> _interactions.EmbeddingVector:
        document_hash = _hashlib.sha256(document.encode()).hexdigest()
        
        datafile = _saves.ConfigurationFile[None | _T.Sequence[float]](self.__directory.get_directory('embeddings').get_resource(document_hash + '.json'), None)
        
        data = datafile.read_configuration()
        
        if data is None:
            vector = discussion.creators_state.create_from_factory(self.__embedder_factory, document_hash, self.__directory)
            datafile.overwrite_with(vector.as_list())
        else:
            vector = _interactions.EmbeddingVector.from_list(data)
        
        return vector
    
    def is_relevant(self, memory_name: str, discussion: _ai_discussion.ChatbotDiscussion, query: str, remembering: ChatbotMemoryRegistry.Remembering) -> bool:
        embedded_query = self.get_embedding(query, discussion)
        embedded_document = self.get_embedding(str(remembering), discussion)
        
        configuration = _saves.ConfigurationFile[_vector_based_memory_configuration_object](self.__directory.get_directory('memory:' + memory_name).get_resource('settings.conf'), {
            'threshold': 0.5
        }).read_configuration()
        
        return _interactions.EmbeddingVector.similarity_between(embedded_query, embedded_document) > configuration['threshold']

