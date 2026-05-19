import typing as _T
import local_utils.images as _local_utils_images
import saves as _saves
import datetime as _datetime
import interactions as _interactions
import json as _json

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
        def __call__(self, directory: _saves.ResourcesDirectory, update_state: _T.Callable[[str], _T.Any], **kwargs) -> str: ...
        
    class ChatCompletionToolResult():
        def __init__(self, time: _datetime.datetime, tool_name: str, args: _T.Mapping[str, _T.Any], result: str) -> None:
            self.__time = time
            self.__tool = tool_name
            self.__args = args
            self.__result = result
            
        @property
        def time(self) -> _datetime.datetime:
            return self.__time
        
        @property
        def tool_name(self) -> str:
            return self.__tool
        
        @property
        def args(self) -> _T.Mapping[str, _T.Any]:
            return self.__args
        
        @property
        def result(self) -> str:
            return self.__result

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

    def __init__(self, name: str, callable: ToolCallable, description: _T.Optional[str]=None, is_ephemeral = False, **parameters: Parameter) -> None:
        self.__name = name
        self.__callable = callable
        self.__description = description
        self.__parameters = parameters
        self.__is_ephemeral = is_ephemeral

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
    
    @property
    def is_ephemeral(self) -> bool:
        return self.__is_ephemeral
    
class ChatCompletionDescription():
    class ToolAdvancementFollower(_T.Protocol):
        def on_tool_started(self, tool: ChatCompletionTool, args: _T.Mapping[str, _T.Any]) -> None:...
        def on_tool_update(self, tool: ChatCompletionTool, args: _T.Mapping[str, _T.Any], event_data: str) -> None:...
        def on_tool_finished(self, tool: ChatCompletionTool, result: ChatCompletionTool.ChatCompletionToolResult) -> None:...
    
    def __init__(self,
                 messages: _T.Sequence[ChatCompletionMessage | ChatCompletionTool.ChatCompletionToolResult],
                 json_schema: _T.Optional[_T.Any] = None, 
                 tools: _T.Optional[_T.Sequence[ChatCompletionTool]] = None,
                 discussion_uuid: _T.Optional[str] = None,
                 tools_advancement_follower: _T.Optional[ToolAdvancementFollower] = None,
                 description_editor: _T.Callable[['ChatCompletionDescription'], 'ChatCompletionDescription'] = lambda self:self
        ) -> None:
        
        self.__discussion_uuid = discussion_uuid
        self.__messages = messages
        self.__json_schema = json_schema
        self.__tools = tools or []
        self.__tools_advancement_follower = tools_advancement_follower
        self.__discussion_editor = description_editor
        
    @property
    def discussion_uuid(self) -> str | None:
        return self.__discussion_uuid
    
    @property
    def messages(self) -> _T.Sequence[ChatCompletionMessage | ChatCompletionTool.ChatCompletionToolResult]:
        return self.__messages
    
    @property
    def json_schema(self) -> _T.Optional[_T.Any]:
        return self.__json_schema
    
    @property
    def tools(self) -> _T.Sequence[ChatCompletionTool]:
        return self.__tools
    
    @property
    def tools_advancement_follower(self) -> ToolAdvancementFollower | None:
        return self.__tools_advancement_follower
    
    @property
    def last_tools_calls(self) -> _T.Sequence[ChatCompletionTool.ChatCompletionToolResult]:
        result: list[ChatCompletionTool.ChatCompletionToolResult] = []
        
        for message in reversed(self.__messages):
            if isinstance(message, ChatCompletionTool.ChatCompletionToolResult):
                result.append(message)
            else:
                break
        
        return list(reversed(result))
    
    @property
    def editor(self) -> _T.Callable[['ChatCompletionDescription'], 'ChatCompletionDescription']:
        return self.__discussion_editor
    
    def get_edited(self) -> 'ChatCompletionDescription':
        return self.__discussion_editor(self)
    
    def removing_messages(self, count_before: int = 0, count_after: int = 0) -> 'ChatCompletionDescription':
        return ChatCompletionDescription(self.__messages[count_before:-count_after], self.__json_schema, self.__tools, self.__discussion_uuid, self.__tools_advancement_follower, self.__discussion_editor)
    
    def adding_message_before(self, *messages: ChatCompletionMessage | ChatCompletionTool.ChatCompletionToolResult) -> 'ChatCompletionDescription':
        return ChatCompletionDescription(list(messages) + list(self.__messages), self.__json_schema, self.__tools, self.__discussion_uuid, self.__tools_advancement_follower, self.__discussion_editor)
    
    def adding_message_just_after_system_prompt(self, *messages: ChatCompletionMessage) -> 'ChatCompletionDescription':
        first_messages = []
        last_messages = list(self.messages)
        
        while last_messages:
            message = last_messages[0]
            
            if isinstance(message, ChatCompletionMessage) and message.role == 'system':
                first_messages.append(last_messages.pop(0))
            else:
                break
        
        return ChatCompletionDescription(first_messages + list(messages) + last_messages, self.__json_schema, self.__tools, self.__discussion_uuid, self.__tools_advancement_follower, self.__discussion_editor)
    
    def adding_message_after(self, *messages: ChatCompletionMessage | ChatCompletionTool.ChatCompletionToolResult) -> 'ChatCompletionDescription':
        return ChatCompletionDescription(list(self.__messages) + list(messages), self.__json_schema, self.__tools, self.__discussion_uuid, self.__tools_advancement_follower, self.__discussion_editor)
    
    def adding_tools(self, *tools: ChatCompletionTool) -> 'ChatCompletionDescription':
        return ChatCompletionDescription(self.__messages, self.__json_schema, list(self.__tools) + list(tools), self.__discussion_uuid, self.__tools_advancement_follower, self.__discussion_editor)
    
    def without_tools(self) -> 'ChatCompletionDescription':
        return ChatCompletionDescription(self.__messages, self.__json_schema, discussion_uuid=self.__discussion_uuid, tools_advancement_follower=self.__tools_advancement_follower, description_editor=self.__discussion_editor)
    
    def without_json_schema(self) -> 'ChatCompletionDescription':
        return ChatCompletionDescription(self.__messages, tools = self.__tools, discussion_uuid=self.__discussion_uuid, tools_advancement_follower=self.__tools_advancement_follower, description_editor=self.__discussion_editor)
    
    def with_json_schema(self, schema) -> 'ChatCompletionDescription':
        return ChatCompletionDescription(self.__messages, schema, self.__tools, self.__discussion_uuid, self.__tools_advancement_follower, self.__discussion_editor)
    
    def without_editor(self) -> 'ChatCompletionDescription':
        return ChatCompletionDescription(self.__messages, self.__json_schema, self.__tools, self.__discussion_uuid, self.__tools_advancement_follower)
    
    def adding_editor_before(self, editor: _T.Callable[['ChatCompletionDescription'], 'ChatCompletionDescription']) -> 'ChatCompletionDescription':
        previous_editor = self.__discussion_editor
        return ChatCompletionDescription(self.__messages, self.__json_schema, self.__tools, self.__discussion_uuid, self.__tools_advancement_follower, lambda self:previous_editor(editor(self)))
    
    def adding_editor_after(self, editor: _T.Callable[['ChatCompletionDescription'], 'ChatCompletionDescription']) -> 'ChatCompletionDescription':
        previous_editor = self.__discussion_editor
        return ChatCompletionDescription(self.__messages, self.__json_schema, self.__tools, self.__discussion_uuid, self.__tools_advancement_follower, lambda self:editor(previous_editor(self)))

class ChatCompletionResult():
    def __init__(self, result: str, tools_results: _T.Sequence[ChatCompletionTool.ChatCompletionToolResult]) -> None:
        self.__result = result
        self.__tools_results = tools_results
    
    @property
    def result(self) -> str:
        return self.__result
    
    @property
    def tools_results(self) -> _T.Sequence[ChatCompletionTool.ChatCompletionToolResult]:
        return self.__tools_results

class ToolCallSaveFile():
    def __init__(self, file: _saves.ResourceFile) -> None:
        self.__file = file
        
    def write_tool_call(self, call: _interactions.ChatCompletionTool.ChatCompletionToolResult) -> None:
        self.__file.write_content(_json.dumps({
            'tool_name': call.tool_name,
            'args': call.args,
            'result': call.result,
            'time': call.time.timestamp()
        }, indent=2))
        
    def read_tool_call(self) -> _interactions.ChatCompletionTool.ChatCompletionToolResult:
        data = _json.loads(self.__file.read_content())
        
        return _interactions.ChatCompletionTool.ChatCompletionToolResult(
            _datetime.datetime.fromtimestamp(data['time'], _datetime.UTC), 
            data['tool_name'],
            data['args'],
            data['result']
        )


