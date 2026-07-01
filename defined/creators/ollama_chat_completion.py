import typing as _T
import json as _json
import httpx as _httpx
import interactions as _interactions
import ollama as _ollama
import saves as _saves
import datetime as _datetime
import asyncio as _asyncio
import threading as _threading

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
                'temperature': 0.5
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

        self.__model_name = model_name
        self.__base_options = base_options
        self.__current_task: _asyncio.Task | None = None
        self.__loop = _asyncio.new_event_loop()

        self.thread = _threading.Thread(target=self._start_loop, daemon=True)
        self.thread.start()

    def _start_loop(self):
        _asyncio.set_event_loop(self.__loop)
        self.__loop.run_forever()

    def on_interruption(self) -> None:
        if self.__current_task is not None:
            self.__current_task.cancel()
            
    def on_finish(self) -> None:
        if self.__loop.is_running():
            self.__loop.call_soon_threadsafe(self.__loop.stop)
            self.thread.join()
            
        self.__loop.close()
        
    def _create_object_from(self, description: _interactions.ChatCompletionDescription) -> _interactions.ChatCompletionResult:
        try:
            result = _asyncio.run_coroutine_threadsafe(self.chat(description), self.__loop).result()
            
            for post_processor in description.post_processors:
                post_processor(result)
                
            return result
                
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

        if usable_tools and description.json_schema:
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
                                },
                                'required': [property_name for property_name, param in tool.parameters.items() if param.is_required],
                            }
                        },
                        'required': ['tool_name'],
                        'additionalProperties': False
                    }
                    for tool in usable_tools
                ]
            }
            
            llm_tools_json_schema = {
                'tool_name': "<the name of the tool to call>",
                'arguments': {
                    "<keys>": "<some values>"
                }
            }

            schema = {
                'oneOf': [
                    description.json_schema,
                    TOOLS_JSON_SCHEMA
                ]
            }
            
            description = description.adding_message_just_after_system_prompt(_interactions.ChatCompletionMessage(
                'system',
                'To call a tool instead of answering, you can directly use the following JSON structure, instead of the other one : \n' + _json.dumps(llm_tools_json_schema) + ". It will be automatically converted to a tool call\n\n" \
                "Here is a list of all tools :\n" \
                '' + '\n\n'.join([
                    f'{_json.dumps(tool.name)}: {tool.description or ""}\n' \
                    f"Parameters: \n" + '\n-'.join([
                        f'{_json.dumps(name)} {": " + param.schema["description"] if "description" in param.schema else ""}'
                        for name, param in tool.parameters.items()
                    ])
                    for tool in usable_tools
                ])
            ))
            
            tools = None
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

        return messages, tools or None, schema

    async def chat(self, description: _interactions.ChatCompletionDescription) -> _interactions.ChatCompletionResult:
        self.__current_task = _asyncio.current_task()
        
        called_tools: list[_interactions.ChatCompletionTool.ChatCompletionToolResult] = []
        while True:
            edited_description = description.get_edited()
            
            tools_by_name = {tool.name: tool for tool in edited_description.tools}
            
            messages, tools, schema = self.get_messages_tools_json(edited_description, description.last_tools_calls)
            
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
            
            self.raise_interruption_if_needed()
            
            for tool_call in message.tool_calls:
                tool = tools_by_name[tool_call.function.name]
                
                if tool.name in [result.tool_name for result in description.last_tools_calls] and tool.is_ephemeral:
                    tool_result = _interactions.ChatCompletionTool.ChatCompletionToolResult(
                        _datetime.datetime.now(_datetime.UTC), 
                        tool.name, 
                        tool_call.function.arguments, 
                        "You cannot call this tool twice. Please now answer to the user. "
                    )
                else:
                    try:
                        if description.tools_advancement_follower:
                            advancement_follower = description.tools_advancement_follower
                            advancement_follower.on_tool_started(tool, tool_call.function.arguments)
                            
                            state_callback = lambda state: advancement_follower.on_tool_update(tool, tool_call.function.arguments, state)
                        else:
                            state_callback = lambda state: None
                        
                        result = tool.callable(state_callback, **tool_call.function.arguments)
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
                
                description = description.adding_message_after(tool_result)

            
