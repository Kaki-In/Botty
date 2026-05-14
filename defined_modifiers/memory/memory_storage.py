import abc as _abc
import typing as _T
import typing_extensions as _TExt

from ai.chatbot_data import ChatbotSpecs
from ai.chatbots import ChatbotDiscussionModifier
from ai.discussion import ChatbotDiscussion

from interactions import CreatorFactory
from defined_creators.used_objects import ChatCompletionDescription, EmbeddingVector

@_TExt.deprecated("implies a lot of incoherences.")
class MemoryStorage[DocumentType](ChatbotDiscussionModifier, _abc.ABC):
    def __init__(self, embedder: CreatorFactory[DocumentType, EmbeddingVector]) -> None:
        super().__init__()
        self.__embedder = embedder

    @property
    def embedder(self) -> CreatorFactory[DocumentType, EmbeddingVector]:
        ...

    @_abc.abstractmethod
    def save_in_memory(self, specs: ChatbotSpecs, discussion: ChatbotDiscussion, document: DocumentType, vector: EmbeddingVector) -> None:
        ...

    @_abc.abstractmethod
    def retrieve_documents(self, specs: ChatbotSpecs, discussion: ChatbotDiscussion, vector: EmbeddingVector) -> _T.Iterable[tuple[float, DocumentType]]:
        ...
    
    @_abc.abstractmethod
    def get_back(self, specs: ChatbotSpecs, discussion: ChatbotDiscussion, document: DocumentType) -> EmbeddingVector:
        ...

    @_abc.abstractmethod
    def extract_documents_from_current_chat_messages(self, specs: ChatbotSpecs, discussion: ChatbotDiscussion, description: ChatCompletionDescription) -> _T.Iterable[DocumentType]:
        ...

    @_abc.abstractmethod
    def remember_documents(self, specs: ChatbotSpecs, discussion: ChatbotDiscussion, documents: _T.Sequence[tuple[float, DocumentType]], description: ChatCompletionDescription) -> ChatCompletionDescription:
        ...

    @_abc.abstractmethod
    def knows(self, specs: ChatbotSpecs, discussion: ChatbotDiscussion, document: DocumentType) -> bool:
        ...

    def modify_chat_completion(self, specs: ChatbotSpecs, discussion: ChatbotDiscussion, description: ChatCompletionDescription) -> ChatCompletionDescription:
        found_docs = self.extract_documents_from_current_chat_messages(specs, discussion, description)
        new_documents = [
            (
                doc, 
                self.get_back(specs, discussion, doc)
                if self.knows(specs, discussion, doc) else
                discussion.creators_state.create_from_factory(self.__embedder, doc, specs.configuration_directory.get_directory('storage_memory'))
            )
            for doc in found_docs
        ]

        old_documents: set[tuple[float, DocumentType]] = set()
        for new_document, vector in new_documents:
            found_documents = self.retrieve_documents(specs, discussion, vector)
            old_documents = old_documents.union(set(found_documents))
        
        old_documents = old_documents.difference(set([document for document, vector in new_documents]))
        
        remembered_documents = sorted(old_documents, reverse=True)

        result = self.remember_documents(specs, discussion, remembered_documents, description)

        for new_document, vector in new_documents:
            self.save_in_memory(specs, discussion, new_document, vector)

        return result

        
        




