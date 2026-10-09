import interactions as _interactions
import typing as _T

from ..chatbot_data import ChatbotSpecs
from ..discussion.discussion import ChatbotDiscussion

from .operation import ChatbotOperation

import abc as _abc

class ChatbotDiscussionModifier(_abc.ABC):
    def __init__(self, *operations: ChatbotOperation) -> None:
        super().__init__()
        
        self.__operations = operations
    
    @property
    def operations(self) -> _T.Sequence[ChatbotOperation]:
        return self.__operations
    
    @_abc.abstractmethod
    def modify_chat_completion(self, specs: ChatbotSpecs, discussion: ChatbotDiscussion, description: _interactions.ChatCompletionDescription) -> _interactions.ChatCompletionDescription:
        ...

