from ai.chatbot_data import ChatbotSpecs
from ai.chatbots import ChatbotDiscussionModifier
from ai.discussion import ChatbotDiscussion

from defined_creators import ChatCompletionDescription, ChatCompletionTool

import typing as _T

class ToolsInserterDiscussionModifier(ChatbotDiscussionModifier):
    def __init__(self, *tools: ChatCompletionTool) -> None:
        self.__tools = tools

    @property
    def tools(self) -> _T.Sequence[ChatCompletionTool]:
        return self.__tools
    
    def modify_chat_completion(self, specs: ChatbotSpecs, discussion: ChatbotDiscussion, description: ChatCompletionDescription) -> ChatCompletionDescription:
        return description.adding_tools(*self.__tools)

