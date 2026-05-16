import typing as _T

import interactions as _interactions
import json as _json
import saves as _saves

class _image_dimensions_object(_T.TypedDict):
    width: int
    height: int

class AIPromptGeneratorFactory(_interactions.CreatorFactory[str, _interactions.ImageSettings]):
    def __init__(self, chat_completor: _interactions.CreatorFactory[_interactions.ChatCompletionDescription, _interactions.ChatCompletionResult]) -> None:
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

class AiPromptGenerator(_interactions.Creator[str, _interactions.ImageSettings]):
    def __init__(self, chat_completor: _interactions.Creator[_interactions.ChatCompletionDescription, _interactions.ChatCompletionResult], image_prompt: str, conf_object: dict[str, _image_dimensions_object]):
        super().__init__()

        self.__chat_completor = chat_completor
        self.__image_prompt = image_prompt
        self.__conf_object = conf_object

    def on_interruption(self) -> None:
        self.__chat_completor.interrupt()

    def _create_object_from(self, description: str) -> _interactions.ImageSettings:
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
                    'enum': list(self.__conf_object.keys())
                }
            },
            'required': ['prompt', 'is_about_user', 'format'],
            'additionalProperties': False
        }

        messages: list[_interactions.ChatCompletionMessage] = [
            _interactions.ChatCompletionMessage('system', self.__image_prompt + "\n\nYou must respect the following JSON Schema : \n" + _json.dumps(schema, indent=2)+"\n\nDon't forget to provide `true` if it is about the character's face."),
            _interactions.ChatCompletionMessage('user', "Here is a basic description of the image: " + description)
        ]

        image_settings = _json.loads(self.__chat_completor._create_object_from(_interactions.ChatCompletionDescription(messages, schema)).result)

        return _interactions.ImageSettings(
            self.__conf_object[image_settings['format']]['width'],
            self.__conf_object[image_settings['format']]['height'],
            image_settings['is_about_user'],
            image_settings['prompt']
        )

