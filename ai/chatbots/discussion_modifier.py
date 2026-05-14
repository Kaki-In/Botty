from defined_creators.used_objects import ChatCompletionDescription

from ai.chatbot_data import ChatbotSpecs
from ai.discussion import ChatbotDiscussion

import abc as _abc

class ChatbotDiscussionModifier(_abc.ABC):
    @_abc.abstractmethod
    def modify_chat_completion(self, specs: ChatbotSpecs, discussion: ChatbotDiscussion, description: ChatCompletionDescription) -> ChatCompletionDescription:
        ...

