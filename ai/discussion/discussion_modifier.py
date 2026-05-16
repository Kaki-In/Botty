import interactions as _interactions

from ..chatbot_data import ChatbotSpecs
from .discussion import ChatbotDiscussion

import abc as _abc

class ChatbotDiscussionModifier(_abc.ABC):
    @_abc.abstractmethod
    def modify_chat_completion(self, specs: ChatbotSpecs, discussion: ChatbotDiscussion, description: _interactions.ChatCompletionDescription) -> _interactions.ChatCompletionDescription:
        ...

