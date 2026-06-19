from ..objects import DiscordChatbotMessage

import interactions as _interactions
import ai.chatbot_data as _ai_chatbot_data

import discord as _discord
import typing as _T
import local_utils.images as _local_utils_images
import saves as _saves
import random as _random

class _discord_textual_message_minmax_object(_T.TypedDict):
    min_value: float
    max_value: float

class _discord_textual_messages_config_object(_T.TypedDict):
    wait_duration: _discord_textual_message_minmax_object
    per_char_duration: _discord_textual_message_minmax_object

class DiscordChatbotTextualMessage(DiscordChatbotMessage, name="text"):
    @classmethod
    def accepts(cls, message: _discord.Message) -> bool:
        # En Discord, message.content est toujours une str (vide si absent)
        return bool(message.content)

    @classmethod
    def class_get_description(cls) -> str:
        return "Sends a text message"

    @classmethod
    def class_get_json_schema(cls):
        return {
            'type': 'string',
            'description': 'The content to write as a single text message.',
            'minLength': 1
        }

    @classmethod
    def class_get_json_description_for_llm(cls) -> str:
        return 'Sends a simple raw text. Example : {"type": "text", "data": "Hello!"}'

    @classmethod
    async def load_from_llm(cls, channel: _discord.TextChannel | _discord.DMChannel, specs: _ai_chatbot_data.ChatbotSpecs, creators: _interactions.CreatorsMap, creators_state: _interactions.CreatorsState, data, answer_to: _T.Optional[int] = None) -> tuple[_discord.Message, _T.Any]:
        assert isinstance(data, str), repr(data)

        messages_configuration = _saves.ConfigurationFile[_discord_textual_messages_config_object](cls.get_bot_discord_configuration(specs).get_resource('config.json'), {
            'wait_duration': {'min_value': 0, 'max_value': 0},
            'per_char_duration': {'min_value': 0, 'max_value': 0},
        }).read_configuration()

        sleeper_directory = cls.get_bot_discord_configuration(specs).get_directory('sleeper')

        await creators.async_create_under_state(
            creators_state,
            _random.uniform(messages_configuration['wait_duration']['min_value'], messages_configuration['wait_duration']['max_value']),
            float,
            _interactions.Sleepy,
            sleeper_directory
        )

        async with channel.typing():
            await creators.async_create_under_state(
                creators_state,
                _random.uniform(messages_configuration['per_char_duration']['min_value'], messages_configuration['per_char_duration']['max_value']) * len(data),
                float,
                _interactions.Sleepy,
                sleeper_directory
            )

        if answer_to:
            reference = _discord.MessageReference(message_id=answer_to, channel_id=channel.id)
            
            new_message = await channel.send(data, reference=reference)
        else:
            new_message = await channel.send(data)
            
        return new_message, None

    def export_data_to_llm(self, specs: _ai_chatbot_data.ChatbotSpecs, images: list[_local_utils_images.Image]):
        return self.discord_message.content