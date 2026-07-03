import ai.chatbot_data as _ai_chatbot_data
import ai.chatbots as _ai_chatbots
import ai.discussion as _ai_discussion

from .memory_factory import ChatbotMemoryFactory
from .memory_registry import ChatbotMemoryRegistry
from .memory_evaluator import ChatbotMemoryEvaluator
from .memory_discussion_modifier import ChatbotMemoryDiscussionModifier

import typing as _T
import interactions as _interactions
import json as _json
import datetime as _datetime
import saves as _saves

class _remembering_response_object(_T.TypedDict):
    sentence: str
    context: dict[str, _T.Any]

class ChatbotMemoryProcessor(_ai_chatbots.ChatbotMessageProcessor):
    def __init__(self, modifier: ChatbotMemoryDiscussionModifier, directory: _saves.ResourcesDirectory, factory: ChatbotMemoryFactory[ChatbotMemoryRegistry, ChatbotMemoryEvaluator], creator_factory: _interactions.CreatorFactory[_interactions.ChatCompletionDescription, _interactions.ChatCompletionResult]) -> None:
        super().__init__()
        
        self.__modifier = modifier
        self.__directory = directory
        self.__factory = factory
        self.__creator_factory = creator_factory
        
    @property
    def modifier(self) -> ChatbotMemoryDiscussionModifier:
        return self.__modifier
    
    @property
    def directory(self) -> _saves.ResourcesDirectory:
        return self.__directory
        
    @property
    def memory_factory(self) -> ChatbotMemoryFactory[ChatbotMemoryRegistry, ChatbotMemoryEvaluator]:
        return self.__factory
    
    @property
    def creator_factory(self) -> _interactions.CreatorFactory[_interactions.ChatCompletionDescription, _interactions.ChatCompletionResult]:
        return self.__creator_factory
    
    def process_message(self, message: _ai_discussion.ChatbotMessage, from_discussion: _ai_discussion.ChatbotDiscussion, specs: _ai_chatbot_data.ChatbotSpecs) -> None:
        state = _interactions.CreatorsState()
        
        memory = self.__factory.get_memory(self.__modifier.name, specs, from_discussion, state)
        
        rememberings_json_schema = {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'sentence': {
                        'type': 'string',
                        'description': 'What should be remembered'
                    },
                    'context': {
                        'type': 'object',
                        'description': 'any context element attached to this remembering'
                    }
                }
            }
        }
        
        prompt_file = self.__directory.get_resource(self.__modifier.name + '.txt')
        
        if not prompt_file.exists:
            prompt_file.write_content("""You are a remembering extractor. 
The user will provide you a message, and you must extract some rememberings to add into the "{name}" memory. 
The memory will then be used according this description : {description}. 

You must include your rememberings into a JSON array containing objects with two keys : 
 - `sentence` : the sentence that describes the remembering
 - `context` : any context element attached to this remembering
""".format(name = self.__modifier.name, description = self.__modifier.description))
        
        images = []
        
        description = _interactions.ChatCompletionDescription(
            [
                _interactions.ChatCompletionMessage('system', prompt_file.read_content()),
                _interactions.ChatCompletionMessage('user', "Please extract some rememberings on this message : \n\n" + str(message.export_to_llm(specs, images)), images)
            ],
            json_schema=rememberings_json_schema
        )
        
        results: list[_remembering_response_object] = _json.loads(state.create_from_factory(self.__creator_factory, description, self.__directory.get_directory('remembering_resolver')).result)
        
        for remembering_description in results:
            memory.registry.save_remembering(memory.registry.Remembering(remembering_description['sentence'], remembering_description['context'], _datetime.datetime.now()))



