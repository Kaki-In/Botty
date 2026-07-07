import ai.discussion as _ai_discussion
import ai.chatbots as _ai_chatbots
import ai.chatbot_data as _ai_chatbot_data

import interactions as _interactions
import typing as _T

from .memory_tool import ChatbotMemoryTool
from .memories_preparator import ChatbotMemoriesPreparator

class ChatbotMemoriesDiscussionModifier(_ai_chatbots.ChatbotDiscussionModifier):
    def __init__(self, memories_preparators: _T.Sequence[ChatbotMemoriesPreparator], provides_tools: bool = True) -> None:
        super().__init__()
        
        self.__provides_tools = provides_tools
        self.__preparators = memories_preparators
        
    @property
    def memory_preparators(self) -> _T.Sequence[ChatbotMemoriesPreparator]:
        return self.__preparators
    
    @property
    def provides_tools(self) -> bool:
        return self.__provides_tools
    
    @provides_tools.setter
    def provides_tools(self, enabled: bool) -> None:
        self.__provides_tools = enabled
        
    def modify_chat_completion(self, specs: _ai_chatbot_data.ChatbotSpecs, discussion: _ai_discussion.ChatbotDiscussion, description: _interactions.ChatCompletionDescription) -> _interactions.ChatCompletionDescription:
        for preparator in self.__preparators:
            all_rememberings = preparator.get_rememberings_for(discussion.creators_state, discussion, specs)
        
            for memory_name, (memory, rememberings) in all_rememberings.items():
                tool = ChatbotMemoryTool(memory_name, memory)
                
                if self.__provides_tools:
                    description = description.adding_tools(tool)
                
                if rememberings:
                    description = description.adding_message_just_after_system_prompt(
                        _interactions.ChatCompletionMessage(
                            'system',
                            f"There are some rememberings you have from memory {memory_name!r} : \n\n" + '\n\n --- \n\n'.join(str(remembering) for remembering in rememberings)
                        )
                    )
        
        return description


