import abc as _abc
import typing as _T

from ..discussion import ChatbotMessage
from ..discussion import ChatbotDiscussion
from ..chatbot_data import ChatbotSpecs, ChatbotOperation

class ChatbotMessageProcessor(_abc.ABC):
    def __init__(self, *operations: ChatbotOperation) -> None:
        super().__init__()
        
        self.__operations = operations
    
    @property
    def operations(self) -> _T.Sequence[ChatbotOperation]:
        return self.__operations
    
    @_abc.abstractmethod
    def process_message(self, message: ChatbotMessage, from_discussion: ChatbotDiscussion, specs: ChatbotSpecs) -> None:
        ...
        
    @_abc.abstractmethod
    def process_messages(self, messages: _T.Sequence[ChatbotMessage], from_discussion: ChatbotDiscussion, specs: ChatbotSpecs) -> None:
        ...
        
