import typing as _T

from interactions import Creator, CreatorFactory
from defined_creators.used_objects import ChatCompletionMessage, ImageSettings, ChatCompletionDescription

import json as _json
import saves as _saves

class _image_dimensions_object(_T.TypedDict):
    width: int
    height: int

class AIPromptGeneratorFactory(CreatorFactory[str, ImageSettings]):
    def __init__(self, chat_completor: CreatorFactory[ChatCompletionDescription, str]) -> None:
        super().__init__()

        self.__chat_completor = chat_completor

    def build_from(self, directory: _saves.ResourcesDirectory) -> 'AiPromptGenerator':
            image_prompt_file = directory.get_resource("image_prompt.txt")

            if not image_prompt_file.exists:
                image_prompt_file.write_content("You are an image creator")

            configuration_file = _saves.ConfigurationFile[dict[str, _image_dimensions_object]](directory.get_resource('sizes.json'), {
                'portrait': {
                    'width': 620,
                    'height': 950
                },
                'landscape': {
                    'width': 950,
                    'height': 520
                }
            })

            return AiPromptGenerator(self.__chat_completor.build_from(directory.get_directory("settings_choosing")), image_prompt_file.read_content(), configuration_file.read_configuration())

class AiPromptGenerator(Creator[str, ImageSettings]):
    def __init__(self, chat_completor: Creator[ChatCompletionDescription, str], image_prompt: str, conf_object: dict[str, _image_dimensions_object]):
        super().__init__()

        self.__chat_completor = chat_completor
        self.__image_prompt = image_prompt
        self.__conf_object = conf_object

    def on_interruption(self) -> None:
        self.__chat_completor.interrupt()

    def _create_object_from(self, description: str) -> ImageSettings:
        schema = {
            'type': 'object',
            'properties': {
                'prompt': {
                    'type': 'string',
                    'description': "A detailed description of the image, suitable for Stable Diffusion. "
                },
                'is_about_user': {
                    'type': 'boolean',
                    'description': "Whether the user describes theirself"
                },
                'format': {
                    'type': 'string',
                    'enum': ['landscape', 'portrait']
                }
            },
            'required': ['prompt', 'is_about_user', 'format'],
            'additionalProperties': False
        }

        messages: list[ChatCompletionMessage] = [
            ChatCompletionMessage('system', self.__image_prompt + "\n\nYou must respect the following JSON Schema : \n" + _json.dumps(schema, indent=2)+"\n\nDon't forget to provide `true` if it is about the character's face."),
            ChatCompletionMessage('user', "Here is a basic description of the image: " + description)
        ]

        image_settings = _json.loads(self.__chat_completor._create_object_from(ChatCompletionDescription(messages, schema)))

        return ImageSettings(
            self.__conf_object[image_settings['format'] + '_size']['width'],
            self.__conf_object[image_settings['format'] + '_size']['height'],
            image_settings['is_about_user'],
            image_settings['prompt']
        )

