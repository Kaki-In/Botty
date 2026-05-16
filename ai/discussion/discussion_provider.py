import abc as _abc
import typing as _T

from .discussion import ChatbotDiscussion
from ..chatbot_data import ChatbotSpecs

class ChatbotDiscussionsProvider(_abc.ABC):
    def __init__(self) -> None:
        super().__init__()

    @_abc.abstractmethod
    def load_all_discussions(self, specs: ChatbotSpecs) -> _T.Sequence[ChatbotDiscussion]:
        ...
    
