import ai.chatbot_data as _ai_chatbot_data
import ai.chatbots as _ai_chatbots
import ai.discussion as _ai_discussion

from .memory_discussion_modifier import ChatbotMemoriesDiscussionModifier

import typing as _T
import interactions as _interactions
import json as _json
import datetime as _datetime
import saves as _saves

class _remembering_response_object(_T.TypedDict):
    sentence: str
    context: dict[str, _T.Any]

class _remembering_configuration_object(_T.TypedDict):
    load_messages_back: int

class ChatbotMemoryProcessor(_ai_chatbots.ChatbotMessageProcessor):
    def __init__(self, modifier: ChatbotMemoriesDiscussionModifier, directory: _saves.ResourcesDirectory, creator_factory: _interactions.CreatorFactory[_interactions.ChatCompletionDescription, _interactions.ChatCompletionResult]) -> None:
        super().__init__()
        
        self.__modifier = modifier
        self.__directory = directory
        self.__creator_factory = creator_factory
        
    @property
    def modifier(self) -> ChatbotMemoriesDiscussionModifier:
        return self.__modifier
    
    @property
    def directory(self) -> _saves.ResourcesDirectory:
        return self.__directory
        
    @property
    def creator_factory(self) -> _interactions.CreatorFactory[_interactions.ChatCompletionDescription, _interactions.ChatCompletionResult]:
        return self.__creator_factory
    
    def process_message(self, message: _ai_discussion.ChatbotMessage, from_discussion: _ai_discussion.ChatbotDiscussion, specs: _ai_chatbot_data.ChatbotSpecs) -> None:
        for preparator in self.__modifier.memory_preparators:
            all_rememberings = preparator.get_rememberings_for(from_discussion, specs)
            
            for memory_name, (memory, rememberings) in all_rememberings.items():
                state = _interactions.CreatorsState()
                
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
                
                prompt_file = self.__directory.get_resource(memory_name + '.txt')
                
                if not prompt_file.exists:
                    prompt_file.write_content("""You are a remembering extractor for {bot_name}. 
The user will provide you a discussion with some messages between {bot_name} and some other users, and you must extract rememberings to create into the "{name}" memory. 
The memory will then be used by {bot_name} according to this description : {description}. 

You must include new rememberings into a JSON array containing objects with two keys : 
- `sentence` : the sentence that describes the remembering
- `context` : any context element attached to this remembering
""".format(bot_name = specs.name, name = memory_name, description = memory.description))
                    
                configuration = _saves.ConfigurationFile[_remembering_configuration_object](self.__directory.get_resource('config.json'), {
                    'load_messages_back': 10
                }).read_configuration()
                
                discussion_messages = "Here are the discussion messages : \n\n"
                
                images=[]
                
                for message in from_discussion.messages[-configuration['load_messages_back']:]:
                    discussion_messages += " - From ({username}) : \n{message}\n\n".format(username=message.sender.export_to_llm(), message=message.export_to_llm(specs, images))
                    
                description = _interactions.ChatCompletionDescription(
                    [
                        _interactions.ChatCompletionMessage('system', prompt_file.read_content()),
                        _interactions.ChatCompletionMessage('user', "Please extract some rememberings on this message : \n\n" + str(message.export_to_llm(specs, images)), images)
                    ],
                    json_schema=rememberings_json_schema
                )
                
                if rememberings:
                    description = description.adding_message_after(
                        _interactions.ChatCompletionMessage(
                            'system',
                            f"There are some rememberings you already have from memory \"{memory_name}\" : \n\n" + '\n\n --- \n\n'.join(str(remembering) for remembering in rememberings) + "\n\nYou must only create new rememberings, if there are some."
                        )
                    )
        
                results: list[_remembering_response_object] = _json.loads(state.create_from_factory(self.__creator_factory, description, self.__directory.get_directory('remembering_resolver')).result)
                
                for remembering_description in results:
                    memory.save_remembering(memory.Remembering(remembering_description['sentence'], remembering_description['context'], _datetime.datetime.now()))



