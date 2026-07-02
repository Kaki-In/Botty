import interactions as _interactions

import ai.chatbot_data as _ai_chatbot_data
import ai.discussion as _ai_discussion

import typing as _T
import saves as _saves

class _memory_query_configuration_object(_T.TypedDict):
    load_messages_back: int

class DiscussionExaminatorFactory(_interactions.CreatorFactory[tuple[_ai_chatbot_data.ChatbotSpecs,_ai_discussion.ChatbotDiscussion, _T.Any], str]):
    def __init__(self, chat_completion_creator_factory: _interactions.CreatorFactory[_interactions.ChatCompletionDescription, _interactions.ChatCompletionResult], default_prompt: str) -> None:
        super().__init__()
        
        self.__chat_completion_creator_factory = chat_completion_creator_factory
        self.__default_prompt = default_prompt
    
    def build_from(self, directory: _saves.ResourcesDirectory) -> _interactions.Creator[tuple[_ai_chatbot_data.ChatbotSpecs, _ai_discussion.ChatbotDiscussion, _T.Any], str]:
        system_prompt = directory.get_resource('prompt.txt')
        
        if not system_prompt.exists:
            system_prompt.write_content(self.__default_prompt)
        
        configuration = _saves.ConfigurationFile[_memory_query_configuration_object](directory.get_resource('conf.json'), {
            'load_messages_back': 10
        }).read_configuration()
        
        return MemoryQueryCreator(self.__chat_completion_creator_factory.build_from(directory.get_directory('chat_completion')), system_prompt.read_content(), configuration)

class MemoryQueryCreator(_interactions.Creator[tuple[_ai_chatbot_data.ChatbotSpecs,_ai_discussion.ChatbotDiscussion[_ai_discussion.ChatbotMessage], _T.Any], str]):
    def __init__(self, chat_completion_factory: _interactions.Creator[_interactions.ChatCompletionDescription, _interactions.ChatCompletionResult], system_prompt: str, configuration: _memory_query_configuration_object) -> None:
        super().__init__()

        self.__chat_completion_factory = chat_completion_factory
        self.__system_prompt = system_prompt
        self.__configuration = configuration

    def _create_object_from(self, description: tuple[_ai_chatbot_data.ChatbotSpecs, _ai_discussion.ChatbotDiscussion[_ai_discussion.ChatbotMessage[_ai_discussion.ChatbotSender]], _T.Any]) -> str:
        specs, discussion, json_schema = description
        
        user_messages = "Here are the discussion messages : \n\n"
        
        images = []
        
        for message in discussion.messages[-self.__configuration['load_messages_back']:]:
            user_messages += " - From ({username}) : \n{message}\n\n".format(username=message.sender.export_to_llm(), message=message.export_to_llm(specs, images))
        
        chat = _interactions.ChatCompletionDescription(
            [
                _interactions.ChatCompletionMessage('system', self.__system_prompt),
                _interactions.ChatCompletionMessage('user', user_messages, images),
            ],
            json_schema=json_schema
        )
        
        return self.__chat_completion_factory.create_object_from(chat).result

