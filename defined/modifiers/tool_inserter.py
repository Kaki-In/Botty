import ai.chatbot_data as _ai_chatbot_data
import ai.discussion as _ai_discussion

import interactions as _interactions

import typing as _T

class ToolsInserterDiscussionModifier(_ai_discussion.ChatbotDiscussionModifier):
    def __init__(self, *tools: _interactions.ChatCompletionTool) -> None:
        self.__tools = tools

    @property
    def tools(self) -> _T.Sequence[_interactions.ChatCompletionTool]:
        return self.__tools
    
    def modify_chat_completion(self, specs: _ai_chatbot_data.ChatbotSpecs, discussion: _ai_discussion.ChatbotDiscussion, description: _interactions.ChatCompletionDescription) -> _interactions.ChatCompletionDescription:
        return description.adding_tools(*self.__tools)

