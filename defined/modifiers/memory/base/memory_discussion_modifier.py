import ai.discussion as _ai_discussion
import ai.chatbot_data as _ai_chatbot_data

import interactions as _interactions
import typing as _T

from .memory import ChatbotMemory
from .memory_tool import ChatbotMemoryTool
from .memory_factory import ChatbotMemoryFactory

class ChatbotMemoryDiscussionModifier(_ai_discussion.ChatbotDiscussionModifier):
    def __init__(self, memory_factory: ChatbotMemoryFactory, query_factory: _interactions.CreatorFactory[tuple[_ai_chatbot_data.ChatbotSpecs,_ai_discussion.ChatbotDiscussion], str], name: str, description: _T.Optional[str] = None) -> None:
        super().__init__()
        
        self.__name = name
        self.__description = description
        self.__factory = query_factory
        self.__memory_factory = memory_factory
        
    @property
    def name(self) -> str:
        return self.__name
    
    @property
    def description(self) -> str | None:
        return self.__description
    
    @property
    def query_factory(self) -> _interactions.CreatorFactory[tuple[_ai_chatbot_data.ChatbotSpecs,_ai_discussion.ChatbotDiscussion], str]:
        return self.__factory
    
    @property
    def memory_factory(self) -> ChatbotMemoryFactory:
        return self.__memory_factory
        
    def get_relevant_memory_query(self, specs: _ai_chatbot_data.ChatbotSpecs, discussion: _ai_discussion.ChatbotDiscussion) -> str:
        return discussion.creators_state.create_from_factory(self.__factory, (specs, discussion), specs.configuration_directory.get_directory('memory:'+self.name).get_directory('discussion2query'))
    
    def modify_chat_completion(self, specs: _ai_chatbot_data.ChatbotSpecs, discussion: _ai_discussion.ChatbotDiscussion, description: _interactions.ChatCompletionDescription) -> _interactions.ChatCompletionDescription:
        memory = self.__memory_factory.get_memory(self.__name, specs, discussion, discussion.creators_state)
        
        elements = memory.remember_from(self.get_relevant_memory_query(specs, discussion), discussion)
        tool = ChatbotMemoryTool(self.__name, memory, self.__description)
        
        description = description.adding_tools(tool)
        
        if not elements:
            return description
        
        return description.adding_message_after(
            _interactions.ChatCompletionMessage(
                'system',
                "You remember about these elements : \n\n" + '\n\n --- \n\n'.join(str(element) for element in elements)
            )
        )


