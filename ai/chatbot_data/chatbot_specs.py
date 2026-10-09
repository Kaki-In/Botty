import saves as _saves
import interactions as _interactions
import abc as _abc
import typing as _T

import ai.chatbots as _ai_chatbots

class ChatbotSpecs(_abc.ABC):
    def __init__(self, name: str, directory: _saves.ResourcesDirectory, message_creator: _interactions.CreatorFactory[_interactions.ChatCompletionDescription, _interactions.ChatCompletionResult]) -> None:
        self.__name = name
        self.__messages_creator = message_creator
        self.__directory = directory
        self.__configuration_directory = directory.get_directory('conf')
        self.__operations = ()
    
    @property
    def name(self) -> str:
        return self.__name

    @property
    def messages_creator(self) -> _interactions.CreatorFactory[_interactions.ChatCompletionDescription, _interactions.ChatCompletionResult]:
        return self.__messages_creator
    
    @property
    def directory(self) -> _saves.ResourcesDirectory:
        return self.__directory

    @property
    def configuration_directory(self) -> _saves.ResourcesDirectory:
        return self.__configuration_directory
    
    @property
    def operations(self) -> _T.Sequence[_ai_chatbots.ChatbotOperation]:
        return self.__operations
    
    def _set_operations(self, operations: _T.Sequence[_ai_chatbots.ChatbotOperation]) -> None:
        self.__operations = operations
    
    def __eq__(self, value: object) -> bool:
        if isinstance(specs:=value, ChatbotSpecs):
            return specs.__directory == self.__directory
        
        return super().__eq__(value)
    
