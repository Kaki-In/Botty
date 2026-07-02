import ai.discussion as _ai_discussion
import ai.chatbots as _ai_chatbots
import ai.chatbot_data as _ai_chatbot_data

import interactions as _interactions
import typing as _T
import json as _json

from .memory_tool import ChatbotMemoryTool
from .memory_factory import ChatbotMemoryFactory
from .memory_evaluator import ChatbotMemoryEvaluator
from .memory_registry import ChatbotMemoryRegistry

class ChatbotMemoryDiscussionModifier(_ai_chatbots.ChatbotDiscussionModifier):
    def __init__(self, memory_factory: ChatbotMemoryFactory[ChatbotMemoryRegistry, ChatbotMemoryEvaluator], query_factory: _interactions.CreatorFactory[tuple[_ai_chatbot_data.ChatbotSpecs, _ai_discussion.ChatbotDiscussion, _T.Any], str], name: str, description: _T.Optional[str] = None, provides_tool: bool = True) -> None:
        super().__init__()
        
        self.__name = name
        self.__description = description
        self.__factory = query_factory
        self.__memory_factory = memory_factory
        self.__provides_tool = provides_tool
        
    @property
    def name(self) -> str:
        return self.__name
    
    @property
    def description(self) -> str | None:
        return self.__description
    
    @property
    def query_factory(self) -> _interactions.CreatorFactory[tuple[_ai_chatbot_data.ChatbotSpecs,_ai_discussion.ChatbotDiscussion, _T.Any], str]:
        return self.__factory
    
    @property
    def memory_factory(self) -> ChatbotMemoryFactory[ChatbotMemoryRegistry, ChatbotMemoryEvaluator]:
        return self.__memory_factory
    
    @property
    def provides_tool(self) -> bool:
        return self.__provides_tool
    
    @provides_tool.setter
    def provides_tool(self, enabled: bool) -> None:
        self.__provides_tool = enabled
        
    def get_relevant_memory_query(self, specs: _ai_chatbot_data.ChatbotSpecs, discussion: _ai_discussion.ChatbotDiscussion) -> str:
        return _json.loads(discussion.creators_state.create_from_factory(self.__factory, (specs, discussion, {'type': 'string'}), specs.configuration_directory.get_directory('memory:'+self.name).get_directory('discussion2query')))
    
    def modify_chat_completion(self, specs: _ai_chatbot_data.ChatbotSpecs, discussion: _ai_discussion.ChatbotDiscussion, description: _interactions.ChatCompletionDescription) -> _interactions.ChatCompletionDescription:
        memory = self.__memory_factory.get_memory(self.__name, specs, discussion, discussion.creators_state)
        
        elements = memory.remember_from(self.get_relevant_memory_query(specs, discussion), discussion)
        tool = ChatbotMemoryTool(self.__name, memory, self.__description)
        
        if self.__provides_tool:
            description = description.adding_tools(tool)
        
        if not elements:
            return description
        
        return description.adding_message_after(
            _interactions.ChatCompletionMessage(
                'system',
                "There are some rememberings you have : \n\n" + '\n\n --- \n\n'.join(str(element) for element in elements)
            )
        )


