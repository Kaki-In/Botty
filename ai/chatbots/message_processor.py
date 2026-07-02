import abc as _abc

from ..discussion.message import ChatbotMessage
from ..discussion.discussion import ChatbotDiscussion
from ..chatbot_data import ChatbotSpecs

class ChatbotMessageProcessor(_abc.ABC):
    @_abc.abstractmethod
    def process_message(self, message: ChatbotMessage, from_discussion: ChatbotDiscussion, specs: ChatbotSpecs) -> None:
        ...
        
