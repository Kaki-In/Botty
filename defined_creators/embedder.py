import httpx as _httpx
import numpy as _numpy

from interactions import Creator, CreatorFactory, InteractionInterruptionError
from .used_objects import EmbeddingVector

from .ollama_chat_completion import _ollama_file_configuration_object

import ollama as _ollama
import saves as _saves

class OllamaEmbedderFactory(CreatorFactory[str, EmbeddingVector]):
    def build_from(self, directory: _saves.ResourcesDirectory) -> 'OllamaEmbedder':
        conf_file = _saves.ConfigurationFile[_ollama_file_configuration_object](directory.get_resource("config.json"), {
            'hostname': 'http://localhost:11434',
            'model_name': '',
            'options': {}
        })
        config = conf_file.read_configuration()

        client = _ollama.Client(config['hostname'])

        return OllamaEmbedder(client, config['model_name'], _ollama.Options(**config['options']))

class OllamaEmbedder(Creator[str, EmbeddingVector]):
    def __init__(self, client: _ollama.Client, model_name: str, base_options: _ollama.Options) -> None:
        super().__init__()

        self.__client = client
#        client.chat(model_name, options=base_options)

        self.__model_name = model_name
        self.__base_options = base_options

    def on_interruption(self) -> None:
        self.__client.close()

    def _create_object_from(self, description: str) -> EmbeddingVector:
        try:
            result = self.__client.embed(model=self.__model_name, input=description, options=self.__base_options, keep_alive=0)
            assert result is not None
        except _httpx.CloseError:
            raise InteractionInterruptionError()
        
        vector = result.embeddings[0]
        
        return EmbeddingVector(_numpy.array(vector))
