from ai.chatbot_data import ChatbotSpecs
from defined_providers.telegram_ai.objects import TelegramChatbotMessage, TelegramActionWaiting
from interactions import CreatorsMap, CreatorsState
from defined_creators import Sleepy

import telegram as _telegram
import telegram.constants as _telegram_constants
import typing as _T
import local_utils.images as _local_utils_images
import saves as _saves
import random as _random

class _telegram_textual_message_minmax_object(_T.TypedDict):
    min_value: float
    max_value: float

class _telegram_textual_messages_config_object(_T.TypedDict):
    wait_duration: _telegram_textual_message_minmax_object
    per_char_duration: _telegram_textual_message_minmax_object

class TelegramChatbotTextualMessage(TelegramChatbotMessage, name="telegram.text"):
    @classmethod
    def accepts(cls, message: _telegram.Message) -> bool:
        return message.text is not None

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
    def class_get_json_schema_for_llm(cls):
        return {
            'type': 'string',
            'description': 'The content to write as a single text message.'
        }
    
    @classmethod
    async def load_from_llm(cls, chat: _telegram.Chat, specs: ChatbotSpecs, creators: CreatorsMap, creators_state: CreatorsState, data, answer_to: _T.Optional[int] = None) -> tuple[_telegram.Message, _T.Any]:
        assert isinstance(data, str), repr(data)

        messages_configuration = _saves.ConfigurationFile[_telegram_textual_messages_config_object](cls.get_bot_tg_configuration(specs).get_resource('config.json'), {
                'wait_duration': {
                    'min_value': 0,
                    'max_value': 0
                },
                'per_char_duration': {
                    'min_value': 0,
                    'max_value': 0
                },
            }).read_configuration()
        
        sleeper_directory = cls.get_bot_tg_configuration(specs).get_directory('sleeper')

        await creators.async_create_under_state(
            creators_state,
            _random.uniform(messages_configuration['wait_duration']['min_value'], messages_configuration['wait_duration']['max_value']),
            float,
            Sleepy,
            sleeper_directory
        )

        with TelegramActionWaiting(chat, _telegram_constants.ChatAction.TYPING):
            await creators.async_create_under_state(
                creators_state,
                _random.uniform(messages_configuration['per_char_duration']['min_value'], messages_configuration['per_char_duration']['max_value']) * len(data),
                float,
                Sleepy,
                sleeper_directory
            )

        return await chat.send_message(data, reply_to_message_id=answer_to), None
    
    def export_data_to_llm(self, specs: ChatbotSpecs, images: list[_local_utils_images.Image]):
        return self.telegram_message.text




