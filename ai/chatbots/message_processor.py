import abc as _abc
import typing as _T

from ..discussion.message import ChatbotMessage
from ..discussion.discussion import ChatbotDiscussion
from ..chatbot_data import ChatbotSpecs

class ChatbotMessageProcessor(_abc.ABC):
    @_abc.abstractmethod
    def process_message(self, message: ChatbotMessage, from_discussion: ChatbotDiscussion, specs: ChatbotSpecs) -> None:
        ...
        
    @_abc.abstractmethod
    def process_messages(self, messages: _T.Sequence[ChatbotMessage], from_discussion: ChatbotDiscussion, specs: ChatbotSpecs) -> None:
        ...
        
