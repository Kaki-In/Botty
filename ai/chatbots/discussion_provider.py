from ai.discussion import ChatbotDiscussion
from ai.chatbot_data import ChatbotSpecs

import abc as _abc
import typing as _T

class ChatbotDiscussionsProvider(_abc.ABC):
    def __init__(self) -> None:
        super().__init__()

    @_abc.abstractmethod
    def load_all_discussions(self, specs: ChatbotSpecs) -> _T.Sequence[ChatbotDiscussion]:
        ...
    
