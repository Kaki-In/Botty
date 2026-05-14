from ai.chatbot_data import ChatbotSpecs
from ai.discussion import ChatbotDiscussion, ChatbotMessage

from interactions import CreatorFactory
from defined_creators.used_objects import ChatCompletionDescription, ChatCompletionMessage, EmbeddingVector

from .memory_storage import MemoryStorage

import json as _json
import saves as _saves
import numpy as _numpy
import typing as _T
import hashlib as _hashlib
import typing_extensions as _TExt

class JsonMemoryDocumentFile():
    def __init__(self, file: _saves.ResourceFile) -> None:
        self.__file = file

    def read_document(self) -> tuple[str, EmbeddingVector]:
        data = _json.loads(self.__file.read_content())
        return data['document'], EmbeddingVector(_numpy.array(data['vector']))
    
    def save_document(self, document: str, vector: EmbeddingVector) -> None:
        self.__file.write_content(_json.dumps({
            'document': document,
            'vector': vector.vector.tolist()
        }, indent=2))

@_TExt.deprecated("implies a lot of incoherences.")
class ConfigMemoryStorage(MemoryStorage[str]):
    def __init__(self, embedder: CreatorFactory[str, EmbeddingVector]) -> None:
        super().__init__(embedder)

    def get_directory_for(self, specs: ChatbotSpecs) -> _saves.ResourcesDirectory:
        return specs.directory.get_directory("storage")

    def save_in_memory(self, specs: ChatbotSpecs, discussion: ChatbotDiscussion, document: str, vector: EmbeddingVector) -> None:
        directory = self.get_directory_for(specs)

        document_hash = _hashlib.sha256(document.encode()).hexdigest()
        document_file = JsonMemoryDocumentFile(directory.get_resource(document_hash + ".json"))
        document_file.save_document(document, vector)

    def get_all_documents(self, specs: ChatbotSpecs) -> _T.Iterable[tuple[str, EmbeddingVector]]:
        directory = self.get_directory_for(specs)

        for file in directory.list_files():
            if not file.startswith('.') and file.endswith('.json'):
                yield JsonMemoryDocumentFile(directory.get_resource(file)).read_document()

    def retrieve_documents(self, specs: ChatbotSpecs, discussion: ChatbotDiscussion, vector: EmbeddingVector) -> _T.Iterable[tuple[float, str]]:
        docs: list[tuple[float, str]] = []

        for document, document_vector in self.get_all_documents(specs):
            if (dist:=EmbeddingVector.similarity_between(vector, document_vector)) > 0.3:
                docs.append((dist, document))
            
        return docs

    def extract_documents_from_current_chat_messages[messageType: ChatbotMessage](self, specs: ChatbotSpecs, discussion: ChatbotDiscussion[ChatbotMessage], description: ChatCompletionDescription) -> _T.Iterable[str]:
        messages = []

        i = len(discussion.messages)-1

        # read again the last chatbots messages if they are last
        while i>0 and (message:=discussion.messages[i]).is_from_self:
            messages.append(message)
            i-=1

        # read user messages
        while i>0 and not (message:=discussion.messages[i]).is_from_self:
            messages.append(message)
            i-=1

        # read chatbots message just earlier
        while i>0 and (message:=discussion.messages[i]).is_from_self:
            messages.append(message)
            i-=1

        messages = [str(message.export_to_llm(specs, [])) for message in discussion.messages]
        return messages
    
    def knows(self, specs: ChatbotSpecs, discussion: ChatbotDiscussion, document: str) -> bool:
        directory = self.get_directory_for(specs)

        document_hash = _hashlib.sha256(document.encode()).hexdigest()
        return directory.get_resource(document_hash + ".json").exists
    
    def get_back(self, specs: ChatbotSpecs, discussion: ChatbotDiscussion, document: str) -> EmbeddingVector:
        directory = self.get_directory_for(specs)

        document_hash = _hashlib.sha256(document.encode()).hexdigest()
        document_file = JsonMemoryDocumentFile(directory.get_resource(document_hash + ".json"))
        return document_file.read_document()[1]

    def remember_documents(self, specs: ChatbotSpecs, discussion: ChatbotDiscussion, documents: _T.Sequence[tuple[float, str]], description: ChatCompletionDescription) -> ChatCompletionDescription:
        discussion_messages = [str(message.export_to_llm(specs, [])) for message in discussion.messages]

        r_documents = [document for distance, document in documents[:10] if not discussion in discussion_messages]

        if not r_documents:
            return description

        print("Remembering documents", r_documents)
        return ChatCompletionDescription([ChatCompletionMessage('system', 'Here are some messages your memory remembers you : \n' + "\n\n----------\n\n".join(r_documents).replace("[img-", "(img-"))]+list(description.messages), description.json_schema)

    

