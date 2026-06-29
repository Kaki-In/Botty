import interactions as _interactions
import typing as _T
import abc as _abc

from .memory import ChatbotMemory

class ChatbotMemoryTool(_interactions.ChatCompletionTool, _abc.ABC):
    def __init__(self, name: str, memory: ChatbotMemory, description: str | None = None, pattern: str = "*") -> None:
        super().__init__("memory." + name, self.remember, description, False,
                         sentence_data = _interactions.ChatCompletionTool.Parameter({
                            'type': 'string',
                            'description': 'What should be remembered',
                            'pattern': pattern
                         }, True),
                         context = _interactions.ChatCompletionTool.Parameter({
                             'type': 'object',
                             'description': 'any context element attached to this remembering'
                         })
        )
        
        self.__memory = memory
        
    @property
    def memory(self) -> ChatbotMemory:
        return self.__memory

    def remember(self, update_state: _T.Callable[[str], _T.Any], **kwargs) -> str:
        memory = self.__memory
        memory.remember_from(kwargs['sentence_data'])
        
        return "element remembered into memory"

