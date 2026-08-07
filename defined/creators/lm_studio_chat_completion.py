import typing as _T
import re as _re
import json as _json
import threading as _threading
import datetime as _datetime
import concurrent.futures as _concurrent_futures

import lmstudio as _lms
import interactions as _interactions
import saves as _saves


class _lmstudio_file_configuration_object(_T.TypedDict):
    hostname: str
    model_name: str
    options: dict[str, _T.Any]
    supports_multimodal: bool


class LMStudioChatCompletorFactory(_interactions.CreatorFactory[_interactions.ChatCompletionDescription, _interactions.ChatCompletionResult]):
    def build_from(self, directory: _saves.ResourcesDirectory) -> 'LMStudioChatCompletor':
        conf_file = _saves.ConfigurationFile[_lmstudio_file_configuration_object](directory.get_resource("config.json"), {
            'hostname': 'localhost:1234',
            'model_name': '',
            'options': {
                'temperature': 0.5,
                'topPSampling': 1,
                'topKSampling': 256,
                'minPSampling': 0.4,
            },
            'supports_multimodal': False
        })
        config = conf_file.read_configuration()

        client = _lms.Client(config['hostname'])
        model = client.llm.model(config['model_name'])

        return LMStudioChatCompletor(client, model, config['options'], config.get('supports_multimodal') or False)

class LMStudioChatCompletor(_interactions.Creator[_interactions.ChatCompletionDescription, _interactions.ChatCompletionResult]):
    __TOOL_REQUEST_PATTERN = _re.compile(r'\[TOOL_REQUEST\](.*?)\[END_TOOL_REQUEST\]', _re.DOTALL)
    __REASONING_END_MARKER_PATTERN = _re.compile(r'__LM_STUDIO_INTERNAL_LSEP_SYNTHETIC_REASONING_END_[0-9a-f]{32}__')
    __THINK_TAG_PATTERN = _re.compile(r'<think>.*?</think>', _re.DOTALL | _re.IGNORECASE)

    def __init__(self, client: _lms.Client, model: _lms.LLM, prediction_config: _T.Mapping[str, _T.Any], supports_multimodal: bool) -> None:
        super().__init__()

        self.__client = client
        self.__model = model
        self.__prediction_config = dict(prediction_config)
        self.__prediction_config['ttl'] = 0
        self.__supports_multimodal = supports_multimodal

        self.__active_stream_lock = _threading.Lock()
        self.__active_stream = None

    def on_interruption(self) -> None:
        with self.__active_stream_lock:
            stream = self.__active_stream

        if stream is not None:
            try:
                stream.cancel()
            except Exception:
                pass

    def on_finish(self) -> None:
        try:
            self.__client.close()
        except Exception:
            pass

    def _create_object_from(self, description: _interactions.ChatCompletionDescription) -> _interactions.ChatCompletionResult:
        result = self.chat(description)

        for post_processor in description.post_processors:
            post_processor(result)

        return result

    def __build_chat(self, messages: _T.Sequence[_interactions.ChatCompletionMessage | _interactions.ChatCompletionTool.ChatCompletionToolResult]) -> _lms.Chat:
        system_parts = [
            message.content for message in messages
            if isinstance(message, _interactions.ChatCompletionMessage) and message.role == 'system'
        ]
        chat = _lms.Chat("\n\n".join(system_parts)) if system_parts else _lms.Chat()

        for message in messages:
            if isinstance(message, _interactions.ChatCompletionTool.ChatCompletionToolResult):
                chat.add_user_message(
                    f"[Résultat de l'outil {_json.dumps(message.tool_name)} "
                    f"appelé avec {_json.dumps(dict(message.args))}] : {message.result}"
                )
                continue

            if message.role == 'system':
                continue
            elif message.role == 'assistant':
                chat.add_assistant_response(message.content)
            else:
                if self.__supports_multimodal and message.images:
                    images = [_lms.prepare_image(bytes(image)) for image in message.images]
                    chat.add_user_message(message.content, images=images)
                else:
                    chat.add_user_message(message.content)

        return chat

    def __strip_reasoning(self, content: str) -> str:
        match = self.__REASONING_END_MARKER_PATTERN.search(content)
        if match is not None:
            content = content[match.end():]
 
        content = self.__THINK_TAG_PATTERN.sub('', content)
 
        return content.strip()

    def __respond(self, chat: _lms.Chat, response_format: _T.Any = None) -> str:
        stream = self.__model.respond_stream(
            chat,
            config=_T.cast(_lms.LlmPredictionConfigDict, self.__prediction_config),
            response_format=response_format,
        )

        with self.__active_stream_lock:
            self.__active_stream = stream

        try:
            for _fragment in stream:
                self.raise_interruption_if_needed()
        except _concurrent_futures._base.CancelledError:
            raise _interactions.InteractionInterruptionError()
        finally:
            with self.__active_stream_lock:
                self.__active_stream = None

        return self.__strip_reasoning(stream.result().content)

    @staticmethod
    def __tool_function_schema(tool: _interactions.ChatCompletionTool) -> dict[str, _T.Any]:
        return {
            'type': 'function',
            'function': {
                'name': tool.name,
                'description': tool.description or '',
                'parameters': {
                    'type': 'object',
                    'properties': {name: param.schema for name, param in tool.parameters.items()},
                    'required': [name for name, param in tool.parameters.items() if param.is_required],
                }
            }
        }

    def __tools_prompt_addition(self, usable_tools: _T.Sequence[_interactions.ChatCompletionTool]) -> str:
        tools_array = {
            'type': 'toolArray',
            'tools': [self.__tool_function_schema(tool) for tool in usable_tools]
        }

        return (
            'You can request calls to available tools with this EXACT format: '
            '[TOOL_REQUEST]{"name": "tool_name", "arguments": {"param1": "value1"}}[END_TOOL_REQUEST]\n'
            'AVAILABLE TOOLS:\n' + _json.dumps(tools_array) + '\n'
            'RULES:\n'
            '- Only use tools from AVAILABLE TOOLS\n'
            '- Include all required arguments\n'
            '- Use one [TOOL_REQUEST] block per tool (you may use several blocks to call several tools)\n'
            '- Never use [TOOL_RESULT]\n'
            '- If you decide to call one or more tools, there should be no other text in your message'
        )

    def __parse_free_tool_requests(self, content: str) -> list[dict[str, _T.Any]]:
        tool_calls: list[dict[str, _T.Any]] = []

        for match in self.__TOOL_REQUEST_PATTERN.finditer(content):
            try:
                parsed = _json.loads(match.group(1))
            except (_json.JSONDecodeError, TypeError):
                continue

            if isinstance(parsed, dict) and 'name' in parsed:
                tool_calls.append({'tool_name': parsed['name'], 'arguments': parsed.get('arguments') or {}})

        return tool_calls

    def __schema_and_tools_response_format(
        self,
        usable_tools: _T.Sequence[_interactions.ChatCompletionTool],
        json_schema: _T.Any,
    ) -> tuple[_T.Any, str]:
        tools_json_schema = {
            'oneOf': [
                {
                    'type': 'object',
                    'properties': {
                        'tool_name': {'type': 'string', 'const': tool.name},
                        'arguments': {
                            'type': 'object',
                            'properties': {name: param.schema for name, param in tool.parameters.items()},
                            'required': [name for name, param in tool.parameters.items() if param.is_required],
                        }
                    },
                    'required': ['tool_name'],
                    'additionalProperties': False
                }
                for tool in usable_tools
            ]
        }

        llm_tools_json_schema = {'tool_name': "<the name of the tool to call>", 'arguments': {"<keys>": "<some values>"}}

        combined_schema = {'oneOf': [json_schema, tools_json_schema]}

        prompt_addition = (
            'To call a tool instead of answering, you can directly use the following JSON structure, '
            'instead of the other one : \n' + _json.dumps(llm_tools_json_schema) +
            ". It will be automatically converted to a tool call\n\n"
            "Here is a list of all tools :\n" + '\n\n'.join([
                f'{_json.dumps(tool.name)}: {tool.description or ""}\n'
                f"Parameters: \n" + '\n-'.join([
                    f'{_json.dumps(name)} {": " + param.schema["description"] if "description" in param.schema else ""}'
                    for name, param in tool.parameters.items()
                ])
                for tool in usable_tools
            ])
        )

        return combined_schema, prompt_addition

    def __parse_schema_tool_calls(self, content: str) -> list[dict[str, _T.Any]]:
        try:
            parsed = _json.loads(content)
        except (_json.JSONDecodeError, TypeError):
            return []

        if isinstance(parsed, dict) and 'tool_name' in parsed:
            return [{'tool_name': parsed['tool_name'], 'arguments': parsed.get('arguments') or {}}]

        return []

    def __execute_tool_call(
        self,
        tool: _interactions.ChatCompletionTool,
        args: _T.Mapping[str, _T.Any],
        description: _interactions.ChatCompletionDescription,
    ) -> _interactions.ChatCompletionTool.ChatCompletionToolResult:
        if tool.is_ephemeral and tool.name in [result.tool_name for result in description.last_tools_calls]:
            return _interactions.ChatCompletionTool.ChatCompletionToolResult(
                _datetime.datetime.now(_datetime.UTC), tool.name, args,
                "You cannot call this tool twice. Please now answer to the user. "
            )

        advancement_follower = description.tools_advancement_follower

        if advancement_follower is not None:
            follower = advancement_follower  # capture locale non-optionnelle pour le narrowing dans la lambda
            follower.on_tool_started(tool, args)
            state_callback = lambda state: follower.on_tool_update(tool, args, state)
        else:
            state_callback = lambda state: None

        try:
            result = tool.callable(state_callback, **args)
        except Exception as exc:
            result = 'An error occured: ' + type(exc).__name__ + ": " + str(exc)

        tool_result = _interactions.ChatCompletionTool.ChatCompletionToolResult(
            _datetime.datetime.now(_datetime.UTC), tool.name, args, result
        )

        if advancement_follower is not None:
            advancement_follower.on_tool_finished(tool, tool_result)

        return tool_result

    def chat(self, description: _interactions.ChatCompletionDescription) -> _interactions.ChatCompletionResult:
        called_tools: list[_interactions.ChatCompletionTool.ChatCompletionToolResult] = []

        while True:
            edited_description = description.get_edited()

            tools_by_name = {tool.name: tool for tool in edited_description.tools}

            already_used_ephemeral = {result.tool_name for result in description.last_tools_calls}
            usable_tools = [
                tool for tool in edited_description.tools
                if not (tool.is_ephemeral and tool.name in already_used_ephemeral)
            ]

            json_schema = edited_description.json_schema

            self.raise_interruption_if_needed()

            if not usable_tools:
                chat = self.__build_chat(edited_description.messages)
                content = self.__respond(chat, json_schema)
                return _interactions.ChatCompletionResult(content, called_tools)

            if json_schema:
                response_format, prompt_addition = self.__schema_and_tools_response_format(usable_tools, json_schema)
            else:
                response_format, prompt_addition = None, self.__tools_prompt_addition(usable_tools)

            prompted_description = edited_description.adding_message_just_after_system_prompt(
                _interactions.ChatCompletionMessage('system', prompt_addition)
            )

            chat = self.__build_chat(prompted_description.messages)
            content = self.__respond(chat, response_format)

            self.raise_interruption_if_needed()

            tool_calls = self.__parse_schema_tool_calls(content) if json_schema else self.__parse_free_tool_requests(content)

            if not tool_calls:
                return _interactions.ChatCompletionResult(content, called_tools)

            self.raise_interruption_if_needed()

            for tool_call in tool_calls:
                tool = tools_by_name.get(tool_call['tool_name'])

                if tool is None:
                    tool_result = _interactions.ChatCompletionTool.ChatCompletionToolResult(
                        _datetime.datetime.now(_datetime.UTC), tool_call['tool_name'], tool_call['arguments'],
                        f"Unknown tool {tool_call['tool_name']!r}."
                    )
                else:
                    tool_result = self.__execute_tool_call(tool, tool_call['arguments'], description)

                called_tools.append(tool_result)
                description = description.adding_message_after(tool_result)