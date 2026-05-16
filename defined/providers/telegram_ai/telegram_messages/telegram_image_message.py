from ..objects import TelegramChatbotMessage, TelegramActionWaiting

import interactions as _interactions
import ai.chatbot_data as _ai_chatbot_data

import telegram as _telegram
import telegram.constants as _telegram_constants
import typing as _T
import local_utils.images as _local_utils_images
import io as _io
import saves as _saves

class TelegramChatbotImageMessage(TelegramChatbotMessage, name="telegram.image"):
    @classmethod
    def class_get_json_schema(cls) -> _T.Any:
        return {
            'type': 'object',
            'properties': {
                'deep_image_description': {
                    'type': 'string',
                    'description': 'a highly detailed description of the image. Should only be factual and contain visual facts. When you are the main character, you must mention it. '
                },
                'caption': {
                    'type': 'string',
                    'description': "the text to provide under the image."
                }
            },
            'required': ['deep_image_description', 'caption'],
            'additionalProperties': False
        }

    @classmethod
    def class_get_json_schema_for_llm(cls) -> _T.Any:
        return {
            'type': 'object',
            'properties': {
                'deep_image_description': {
                    'type': 'string',
                    'description': 'a highly detailed description of the image. Should only be factual and contain visual facts. When you are the main character, you must mention it. '
                },
                'caption': {
                    'type': 'string',
                    'description': "the text to provide under the image."
                }
            }
        }

    @classmethod
    def class_get_description(cls) -> str:
        return "Creates an image with an image generator, from the provided context, and sends it."

    @classmethod
    def accepts(cls, message: _telegram.Message) -> bool:
        return message.photo is not None and len(message.photo) > 0
    
    @classmethod
    async def load_from_llm(cls, chat: _telegram.Chat, specs: _ai_chatbot_data.ChatbotSpecs, creators: _interactions.CreatorsMap, creators_state: _interactions.CreatorsState, data, answer_to: _T.Optional[int] = None) -> tuple[_telegram.Message, _T.Any]:
        assert isinstance(data, dict)

        with TelegramActionWaiting(chat, _telegram_constants.ChatAction.UPLOAD_PHOTO):
            image = await creators.async_create_under_state(creators_state, data['deep_image_description'], str, _local_utils_images.Image, cls.get_bot_tg_configuration(specs).get_directory('image_creation'))

        photo_file = _io.BytesIO(bytes(image))

        return await chat.send_photo(photo_file, caption=data['caption'], reply_to_message_id=answer_to), {
            'image': image,
            'description': data['deep_image_description']
        }
    
    @classmethod
    async def create_with_extras(cls, message: _telegram.Message, specs: _ai_chatbot_data.ChatbotSpecs, extras, directory: _saves.ResourcesDirectory) -> _T.Self:
        image_file = directory.get_resource('image.png')
        image_file.write_raw(bytes(extras['image']))

        description_file = directory.get_resource('description.txt')
        description_file.write_content(extras['description'])

        return cls(message, True, directory)
    
    @classmethod
    async def create_from_telegram(cls, message: _telegram.Message, specs: _ai_chatbot_data.ChatbotSpecs, creators: _interactions.CreatorsMap, creators_state: _interactions.CreatorsState, directory: _saves.ResourcesDirectory) -> _T.Self:
        photo = message.photo[-1]

        photo_file =  _io.BytesIO()
        await (await photo.get_file()).download_to_memory(photo_file)

        image_file = directory.get_resource('image.png')
        image_file.write_raw(photo_file.getvalue())

        image = await _local_utils_images.from_bytes(photo_file.getvalue())
        description = await creators.async_create_under_state(creators_state, image, _local_utils_images.Image, str, cls.get_bot_tg_configuration(specs).get_directory('image_description'))
    
        description_file = directory.get_resource('description.txt')
        description_file.write_content(description)

        return cls(message, False, directory)
    
    @property
    def image(self) -> _local_utils_images.Image:
        return _local_utils_images.long_from_bytes(self._directory.get_resource('image.png').read_raw())
    
    @property
    def description(self) -> str:
        return self._directory.get_resource('description.txt').read_content()

    def export_data_to_llm(self, specs: _ai_chatbot_data.ChatbotSpecs, images: list[_local_utils_images.Image]):
        images.append(self.image)

        return {
            'image': f'[img]',
            'description': self.description,
            'caption': self.telegram_message.caption
        }

