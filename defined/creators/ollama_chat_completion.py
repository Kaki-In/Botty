import typing as _T
import json as _json
import httpx as _httpx
import interactions as _interactions
import ollama as _ollama
import saves as _saves
import datetime as _datetime
import asyncio as _asyncio

class _ollama_file_configuration_object(_T.TypedDict):
    hostname: str
    model_name: str
    options: dict[str, _T.Any]

class OllamaChatCompletorFactory(_interactions.CreatorFactory[_interactions.ChatCompletionDescription, _interactions.ChatCompletionResult]):
    def build_from(self, directory: _saves.ResourcesDirectory) -> 'OllamaChatCompletor':
        conf_file = _saves.ConfigurationFile[_ollama_file_configuration_object](directory.get_resource("config.json"), {
            'hostname': 'http://localhost:11434',
            'model_name': '',
            'options': {
                'min_p': 0.4,
                'top_p': 1,
                'top_k': 256,
                'temperature': 0.9
            }
        })
        config = conf_file.read_configuration()

        client = _ollama.AsyncClient(config['hostname'])

        return OllamaChatCompletor(client, config['model_name'], _ollama.Options(**config['options']), directory)

class OllamaChatCompletor(_interactions.Creator[_interactions.ChatCompletionDescription, _interactions.ChatCompletionResult]):
    def __init__(self, client: _ollama.AsyncClient, model_name: str, base_options: _ollama.Options, directory: _saves.ResourcesDirectory) -> None:
        super().__init__()

        self.__client = client
#        client.chat(model_name, options=base_options)
        self.__directory = directory

        self.__model_name = model_name
        self.__base_options = base_options
        self.__current_task: _asyncio.Task | None = None
        self.__loop = _asyncio.new_event_loop()

    def on_interruption(self) -> None:
        if self.__current_task is not None:
            self.__current_task.cancel()

    def _create_object_from(self, description: _interactions.ChatCompletionDescription) -> _interactions.ChatCompletionResult:
        try:
            return self.__loop.run_until_complete(self.chat(description))
        except (_httpx.CloseError, _asyncio.CancelledError):
            raise _interactions.InteractionInterruptionError()
    
    def get_messages_tools_json(self, description: _interactions.ChatCompletionDescription, runtime_tools_results: _T.Sequence[_interactions.ChatCompletionTool.ChatCompletionToolResult]) -> tuple[_T.Sequence[_ollama.Message], None | _T.Sequence[_ollama.Tool], _T.Any]:
        usable_tools = [tool for tool in description.tools if not (tool.is_ephemeral and tool.name in [result.tool_name for result in runtime_tools_results])]

        if len(usable_tools) > 0:
            tools = [
                _ollama.Tool(
                    function=_ollama.Tool.Function(
                        name=tool.name,
                        description=tool.description,
                        parameters=_ollama.Tool.Function.Parameters(
                            type='object',
                            properties={
                                name: param.schema
                                for name, param in tool.parameters.items()
                            },
                            **{'$defs':None},
                            required=[name for name, param in tool.parameters.items() if param.is_required]
                        )
                    )
                ) for tool in usable_tools
            ]
        else:
            tools = None

        if tools and description.json_schema:
            TOOLS_JSON_SCHEMA = {
                'oneOf': [
                    {
                        'type': 'object',
                        'properties': {
                            'tool_name': {
                                'type': 'string',
                                'const': tool.name
                            },
                            'arguments': {
                                'type': 'object',
                                'properties': {
                                    property_name: param.schema
                                    for property_name, param in tool.parameters.items()
                                }
                            }
                        },
                        'required': [property_name for property_name, param in tool.parameters.items() if param.is_required],
                        'additionalProperties': False
                    }
                    for tool in usable_tools
                ]
            }
            
            llm_tools_json_schema = {
                'type': 'object',
                'properties': {
                    'tool_name': {
                        'type': 'string',
                        'description': 'the name of the tool you need to call'
                    },
                    'arguments': {
                        'type': 'object',
                        'description': 'the arguments provided to the tool'
                    }
                },
                'required': ['tool_name'],
                'additionalProperties': False
            }

            schema = {
                'oneOf': [
                    description.json_schema,
                    TOOLS_JSON_SCHEMA
                ]
            }
            
            description = description.adding_message_just_after_system_prompt(_interactions.ChatCompletionMessage('system', 'To call a tool, you can use the following JSON Schema : \n' + _json.dumps(llm_tools_json_schema)))
        else:
            schema = description.json_schema
        
        messages = []
        
        for message in description.messages:
            if isinstance(message, _interactions.ChatCompletionTool.ChatCompletionToolResult):
                messages.append(_ollama.Message(role='assistant', tool_calls = [
                    _ollama.Message.ToolCall(
                        function=_ollama.Message.ToolCall.Function(
                            name=message.tool_name,
                            arguments=message.args
                        )
                    )
                ]))
                messages.append(_ollama.Message(role='tool', content=message.result))
            else:
                messages.append(_ollama.Message(role=message.role, content=message.content, images = [_ollama.Image(value=bytes(image)) for image in message.images]))

        return messages, tools, schema

    async def chat(self, description: _interactions.ChatCompletionDescription) -> _interactions.ChatCompletionResult:
        self.__current_task = _asyncio.current_task()
        
        tools_by_name = {tool.name: tool for tool in description.tools}
        
        if description.discussion_uuid:
            tools_directory = self.__directory.get_directory('discussion_' + description.discussion_uuid)
        else:
            tools_directory = self.__directory
            
        called_tools: list[_interactions.ChatCompletionTool.ChatCompletionToolResult] = []
        
        while True:
            messages, tools, schema = self.get_messages_tools_json(description, called_tools)
            messages = list(messages)
            
            self.raise_interruption_if_needed()
            
            response = await self.__client.chat(
                model=self.__model_name,
                messages=messages,
                options=self.__base_options,
                format=schema,
                think=False,
                keep_alive=0,
                tools=tools
            )
            
            self.raise_interruption_if_needed()
            
            message = response.message
            
            if message.content:
                try:
                    tool_call = _json.loads(message.content)
                    if isinstance(tool_call, dict) and 'tool_name' in tool_call:
                        message.content = None
                        message.tool_calls = list(message.tool_calls or []) + [
                            _ollama.Message.ToolCall(
                                function = _ollama.Message.ToolCall.Function(
                                    name = tool_call['tool_name'],
                                    arguments = tool_call.get('arguments') or {}
                                )
                            )
                        ]
                except:
                    pass
            
            if not message.tool_calls:
                return _interactions.ChatCompletionResult(message.content or '', called_tools)
            
            messages.append(message)
            
            self.raise_interruption_if_needed()
            
            for tool_call in message.tool_calls:
                tool = tools_by_name[tool_call.function.name]
                
                tool_directory = tools_directory.get_directory(tool.name)
                
                try:
                    if description.tools_advancement_follower:
                        advancement_follower = description.tools_advancement_follower
                        advancement_follower.on_tool_started(tool, tool_call.function.arguments)
                        
                        state_callback = lambda state: advancement_follower.on_tool_update(tool, tool_call.function.arguments, state)
                    else:
                        state_callback = lambda state: None
                    
                    result = tool.callable(tool_directory, state_callback, **tool_call.function.arguments)
                except Exception as exc:
                    result = 'An error occured: ' + type(exc).__name__ + ": " + str(exc)
                    
                tool_result = _interactions.ChatCompletionTool.ChatCompletionToolResult(
                    _datetime.datetime.now(_datetime.UTC), 
                    tool.name, 
                    tool_call.function.arguments, 
                    result
                )
                    
                if description.tools_advancement_follower:
                    description.tools_advancement_follower.on_tool_finished(tool, tool_result)
                
                called_tools.append(tool_result)
                
                messages.append(_ollama.Message(
                    role='tool',
                    content=result
                ))

            
