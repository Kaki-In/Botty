import typing as _T
import json as _json
import httpx as _httpx

from interactions import Creator, CreatorFactory, InteractionInterruptionError
from .used_objects import ChatCompletionDescription

import ollama as _ollama
import saves as _saves

class _ollama_file_configuration_object(_T.TypedDict):
    hostname: str
    model_name: str
    options: dict[str, _T.Any]

class OllamaChatCompletorFactory(CreatorFactory[ChatCompletionDescription, str]):
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

        client = _ollama.Client(config['hostname'])

        return OllamaChatCompletor(client, config['model_name'], _ollama.Options(**config['options']))

class OllamaChatCompletor(Creator[ChatCompletionDescription, str]):
    def __init__(self, client: _ollama.Client, model_name: str, base_options: _ollama.Options) -> None:
        super().__init__()

        self.__client = client
#        client.chat(model_name, options=base_options)

        self.__model_name = model_name
        self.__base_options = base_options

    def on_interruption(self) -> None:
        self.__client.close()

    def _create_object_from(self, description: ChatCompletionDescription) -> str:
        messages = [
            _ollama.Message(role=message.role, content=message.content, images = [_ollama.Image(value=bytes(image)) for image in message.images])
            for message in description.messages
        ]

        if len(description.tools) > 0:
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
                ) for tool in description.tools
            ]
        else:
            tools = None

        try:
            result = self.__client.chat(model=self.__model_name, messages=messages, options=self.__base_options, format=description.json_schema, think=False, keep_alive=0, tools=tools).message.content
            assert result is not None
        except _httpx.CloseError:
            raise InteractionInterruptionError()
        
        self.raise_interruption_if_needed()
        
        print(_json.dumps(description.json_schema), result)

        return result


