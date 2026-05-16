import typing as _T
import local_utils.images as _local_utils_images
import saves as _saves

class ChatCompletionMessage():
    def __init__(self, role: str, content: str, images: _T.Optional[_T.Sequence[_local_utils_images.Image]] = None):
        self.__role = role
        self.__content = content
        self.__images = images or []

    @property
    def role(self) -> str:
        return self.__role
    
    @property
    def content(self) -> str:
        return self.__content
    
    @property
    def images(self) -> _T.Sequence[_local_utils_images.Image]:
        return self.__images

class ChatCompletionTool():
    class ToolCallable(_T.Protocol):
        def __call__(self, directory: _saves.ResourcesDirectory, **kwargs) -> str: ...

    class Parameter():
        def __init__(self, schema: _T.Any, required: bool = True) -> None:
            self.__schema = schema
            self.__required = required

        @property
        def schema(self) -> _T.Any:
            return self.__schema
        
        @property
        def is_required(self) -> bool:
            return self.__required

    def __init__(self, name: str, callable: ToolCallable, description: _T.Optional[str]=None, **parameters: Parameter) -> None:
        self.__name = name
        self.__callable = callable
        self.__description = description
        self.__parameters = parameters

    @property
    def name(self) -> str:
        return self.__name
    
    @property
    def callable(self) -> _T.Callable:
        return self.__callable
    
    @property
    def description(self) -> str | None:
        return self.__description
    
    @property
    def parameters(self) -> _T.Mapping[str, Parameter]:
        return self.__parameters
    
class ChatCompletionDescription():
    def __init__(self, messages: _T.Sequence[ChatCompletionMessage], json_schema: _T.Optional[_T.Any] = None, tools: _T.Optional[_T.Sequence[ChatCompletionTool]] = None) -> None:
        self.__messages = messages
        self.__json_schema = json_schema
        self.__tools = tools or []
    
    @property
    def messages(self) -> _T.Sequence[ChatCompletionMessage]:
        return self.__messages
    
    @property
    def json_schema(self) -> _T.Optional[_T.Any]:
        return self.__json_schema
    
    @property
    def tools(self) -> _T.Sequence[ChatCompletionTool]:
        return self.__tools
    
    def removing_messages(self, count_before: int = 0, count_after: int = 0) -> 'ChatCompletionDescription':
        return ChatCompletionDescription(self.__messages[count_before:-count_after], self.__json_schema, self.__tools)
    
    def adding_message_before(self, *messages: ChatCompletionMessage) -> 'ChatCompletionDescription':
        return ChatCompletionDescription(list(messages) + list(self.__messages), self.__json_schema, self.__tools)
    
    def adding_message_after(self, *messages: ChatCompletionMessage) -> 'ChatCompletionDescription':
        return ChatCompletionDescription(list(self.__messages) + list(messages), self.__json_schema, self.__tools)
    
    def adding_tools(self, *tools: ChatCompletionTool) -> 'ChatCompletionDescription':
        return ChatCompletionDescription(self.__messages, self.__json_schema, list(self.__tools) + list(tools))
    
    def without_tools(self) -> 'ChatCompletionDescription':
        return ChatCompletionDescription(self.__messages, self.__json_schema)
    
    def without_json_schema(self) -> 'ChatCompletionDescription':
        return ChatCompletionDescription(self.__messages, tools = self.__tools)

