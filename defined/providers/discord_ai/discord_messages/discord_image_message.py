from ..objects import DiscordChatbotMessage

import interactions as _interactions
import ai.chatbot_data as _ai_chatbot_data

import discord as _discord
import typing as _T
import local_utils.images as _local_utils_images
import io as _io
import saves as _saves


class DiscordChatbotImageMessage(DiscordChatbotMessage, name="image"):
    @classmethod
    def class_get_json_schema(cls) -> _T.Any:
        return {
            'type': 'object',
            'properties': {
                'deep_image_description': {
                    'type': 'string',
                    'description': 'a highly detailed description of the image. Should only be factual and contain visual facts. When you are the main character, you must mention it.'
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
    def class_get_json_description_for_llm(cls) -> str:
        return 'Generates and includes an image from its description. Example : {"type": "image", "data": {"deep_image_description": "a man walking in space", "caption": "Look ! "}}. '

    @classmethod
    def class_get_description(cls) -> str:
        return "Creates an image with an image generator, from the provided context, and sends it."

    @classmethod
    def accepts(cls, message: _discord.Message) -> bool:
        return len(message.attachments) > 0 and any(
            att.content_type and att.content_type.startswith('image/')
            for att in message.attachments
        )

    @classmethod
    async def load_from_llm(cls, channel: _discord.TextChannel | _discord.DMChannel, specs: _ai_chatbot_data.ChatbotSpecs, creators: _interactions.CreatorsMap, creators_state: _interactions.CreatorsState, data, answer_to: _T.Optional[int] = None) -> tuple[_discord.Message, _T.Any]:
        assert isinstance(data, dict)

        image = await creators.async_create_under_state(
            creators_state,
            data['deep_image_description'],
            str,
            _local_utils_images.Image,
            cls.get_bot_discord_configuration(specs).get_directory('image_creation')
        )

        photo_file = _discord.File(
            fp=_io.BytesIO(bytes(image)),
            filename='image.png'
        )

        kwargs = {'content': data['caption'], 'file': photo_file}
        if answer_to is not None:
            kwargs['reference'] = _discord.MessageReference(
                message_id=answer_to,
                channel_id=channel.id
            )

        sent_message = await channel.send(**kwargs)

        return sent_message, {
            'image': image,
            'description': data['deep_image_description']
        }
        
    @classmethod
    async def create_with_extras(cls, message: _discord.Message, specs: _ai_chatbot_data.ChatbotSpecs, extras, directory: _saves.ResourcesDirectory) -> _T.Self:
        image_file = directory.get_resource('image.png')
        image_file.write_raw(bytes(extras['image']))

        description_file = directory.get_resource('description.txt')
        description_file.write_content(extras['description'])

        return cls(message, directory)

    @classmethod
    async def create_from_discord(cls, message: _discord.Message, specs: _ai_chatbot_data.ChatbotSpecs, creators: _interactions.CreatorsMap, creators_state: _interactions.CreatorsState, directory: _saves.ResourcesDirectory) -> _T.Self:
        attachment = next(
            att for att in message.attachments
            if att.content_type and att.content_type.startswith('image/')
        )

        photo_bytes = await attachment.read()

        image_file = directory.get_resource('image.png')
        image_file.write_raw(photo_bytes)

        image = await _local_utils_images.from_bytes(photo_bytes)
        
        description_file = directory.get_resource('description.txt')
        description_file.write_content("Image description not available yet")
        
        description = await creators.async_create_under_state(
            creators_state,
            image,
            _local_utils_images.Image,
            str,
            cls.get_bot_discord_configuration(specs).get_directory('image_description')
        )

        description_file.write_content(description)

        return cls(message, directory)

    @property
    def image(self) -> _local_utils_images.Image:
        return _local_utils_images.long_from_bytes(
            self._directory.get_resource('image.png').read_raw()
        )

    @property
    def description(self) -> str:
        return self._directory.get_resource('description.txt').read_content()

    def export_data_to_llm(
        self,
        specs: _ai_chatbot_data.ChatbotSpecs,
        images: list[_local_utils_images.Image]
    ):
        images.append(self.image)

        return {
            'image': '[img]',
            'description': self.description,
            'caption': self.discord_message.content
        }