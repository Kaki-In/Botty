import saves as _saves
import interactions as _interaction

class ChatbotSpecs():
    def __init__(self, directory: _saves.ResourcesDirectory, message_creator: _interaction.CreatorFactory[_interaction.ChatCompletionDescription, str]) -> None:
        self.__messages_creator = message_creator
        self.__directory = directory
        self.__configuration_directory = directory.get_directory('conf')

    @property
    def messages_creator(self) -> _interaction.CreatorFactory[_interaction.ChatCompletionDescription, str]:
        return self.__messages_creator
    
    @property
    def directory(self) -> _saves.ResourcesDirectory:
        return self.__directory

    @property
    def configuration_directory(self) -> _saves.ResourcesDirectory:
        return self.__configuration_directory
    
    def __eq__(self, value: object) -> bool:
        if isinstance(specs:=value, ChatbotSpecs):
            return specs.__directory == self.__directory
        
        return super().__eq__(value)
