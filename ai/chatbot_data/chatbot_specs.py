import saves as _saves

from interactions import CreatorFactory
from defined_creators.used_objects import ChatCompletionDescription

class ChatbotSpecs():
    def __init__(self, directory: _saves.ResourcesDirectory, message_creator: CreatorFactory[ChatCompletionDescription, str]) -> None:
        self.__messages_creator = message_creator
        self.__directory = directory
        self.__configuration_directory = directory.get_directory('conf')

    @property
    def messages_creator(self) -> CreatorFactory[ChatCompletionDescription, str]:
        return self.__messages_creator
    
    @property
    def directory(self) -> _saves.ResourcesDirectory:
        return self.__directory

    @property
    def configuration_directory(self) -> _saves.ResourcesDirectory:
        return self.__configuration_directory
    
    
