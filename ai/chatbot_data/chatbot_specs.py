import saves as _saves
import interactions as _interactions
import typing as _T
import uuid as _uuid
import abc as _abc

from .tool_call_savefile import ToolCallSaveFile

class ChatbotSpecs(_abc.ABC):
    def __init__(self, directory: _saves.ResourcesDirectory, message_creator: _interactions.CreatorFactory[_interactions.ChatCompletionDescription, _interactions.ChatCompletionResult]) -> None:
        self.__messages_creator = message_creator
        self.__directory = directory
        self.__configuration_directory = directory.get_directory('conf')
        self.__tool_calls_directory = self.__directory.get_directory('calls')

    @property
    def messages_creator(self) -> _interactions.CreatorFactory[_interactions.ChatCompletionDescription, _interactions.ChatCompletionResult]:
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
    
    def read_tool_calls(self, discussion_uuid: str) -> _T.Sequence[_interactions.ChatCompletionTool.ChatCompletionToolResult]:
        tools: list[_interactions.ChatCompletionTool.ChatCompletionToolResult] = []
        
        directory = self.__tool_calls_directory.get_directory(discussion_uuid)
        
        for filename in directory.list_files():
            file = ToolCallSaveFile(directory.get_resource(filename))
            tools.append(file.read_tool_call())
        
        return tools
    
    def save_tool_calls(self, discussion_uuid: str, tool_calls: _T.Sequence[_interactions.ChatCompletionTool.ChatCompletionToolResult]) -> None:
        directory = self.__tool_calls_directory.get_directory(discussion_uuid)
        
        for tool_call in tool_calls:
            file = ToolCallSaveFile(directory.get_resource(_uuid.uuid4().hex+'.json'))
            file.write_tool_call(tool_call)
