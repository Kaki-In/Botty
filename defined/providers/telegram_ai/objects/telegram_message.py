from .telegram_sender import TelegramChatbotSender

import interactions as _interactions
import ai.discussion as _ai_discussion, ai.chatbot_data as _ai_chatbot_data

import abc as _abc
import telegram as _telegram
import telegram.constants as _telegram_constants
import typing as _T
import local_utils.images as _local_utils_images
import saves as _saves

class TelegramChatbotMessage(_ai_discussion.ChatbotMessage[TelegramChatbotSender], _abc.ABC):
    @classmethod
    @_abc.abstractmethod
    def class_get_description(cls) -> str:
        ...

    @classmethod
    @_abc.abstractmethod
    def accepts(cls, message: _telegram.Message) -> bool:
        ...

    @classmethod
    def is_for_me(cls, message: _telegram.Message) -> bool:
        bot_user = message.chat.get_bot()._bot_user
        assert bot_user and bot_user.username

        if message.reply_to_message and message.reply_to_message.from_user and message.reply_to_message.from_user.id == bot_user.id:
            return True

        bot_user_mention = "@"+bot_user.username

        for entities, text in (
            (message.entities, message.text),
            (message.caption_entities, message.caption)
        ):
            if not entities or not text:
                continue

            for e in entities:
                entity_text = text[e.offset:e.offset + e.length]

                if e.type == "mention" and entity_text.lower() == bot_user_mention:
                    return True

                if e.type == "text_mention":
                    return True  # bot est explicitement ciblé

                if e.type == "bot_command" and entity_text.lower().endswith(bot_user_mention):
                    return True

        return False
    
    @classmethod
    @_abc.abstractmethod
    def class_get_json_schema(cls) -> _T.Any:
        ...
    
    @classmethod
    @_abc.abstractmethod
    def class_get_json_schema_for_llm(cls) -> _T.Any:
        ...
    
    @classmethod
    @_abc.abstractmethod
    async def load_from_llm(cls, chat: _telegram.Chat, specs: _ai_chatbot_data.ChatbotSpecs, creators: _interactions.CreatorsMap, creators_state: _interactions.CreatorsState, data, answer_to: _T.Optional[int] = None) -> tuple[_telegram.Message, _T.Any]:
        ...

    @classmethod
    async def create_with_extras(cls, message: _telegram.Message, specs: _ai_chatbot_data.ChatbotSpecs, extras, directory: _saves.ResourcesDirectory) -> _T.Self:
        return cls(message, directory)
    
    @classmethod
    async def create_from_telegram(cls, message: _telegram.Message, specs: _ai_chatbot_data.ChatbotSpecs, creators: _interactions.CreatorsMap, creators_state: _interactions.CreatorsState, directory: _saves.ResourcesDirectory) -> _T.Self:
        return cls(message, directory)
    
    @classmethod
    def load_back(cls, message: _telegram.Message, directory: _saves.ResourcesDirectory) -> _T.Self:
        return cls(message, directory)

    def __init__(self, message: _telegram.Message, directory: _saves.ResourcesDirectory) -> None:
        assert message.from_user

        bot = message.get_bot()
        assert bot._bot_user

        sender = TelegramChatbotSender(message.from_user, bot._bot_user.id == message.from_user.id)

        super().__init__(str(message.id), message.date, sender)

        self.__message = message
        self.__directory = directory
    
    @property
    def telegram_message(self) -> _telegram.Message:
        return self.__message
    
    @property
    def _directory(self) -> _saves.ResourcesDirectory:
        return self.__directory
    
    @property
    def replies_to(self) -> int | None:
        if self.__message.reply_to_message is None:
            return None
        
        return self.__message.reply_to_message.id
    
    def export_to_llm(self, specs: _ai_chatbot_data.ChatbotSpecs, images: list[_local_utils_images.Image]) -> _T.Any:
        data = {
            'message_id': self.telegram_message.id,
            'type': self.class_get_messages_typename(),
            'data': self.export_data_to_llm(specs, images),
            'sender': self.sender.export_to_llm(),
            'date': self.time.strftime("%A %d/%m/%Y, %H:%M")
        }

        if self.__message.reply_to_message is not None:
            data['replying_to_message'] = self.__message.reply_to_message.id

        if self.__message.chat.type != _telegram_constants.ChatType.PRIVATE:
            data['is_especially_for_me'] = self.is_for_me(self.__message)

        return data
    
    @classmethod
    def get_bot_tg_configuration(cls, specs: _ai_chatbot_data.ChatbotSpecs) -> _saves.ResourcesDirectory:
        return specs.directory.get_directory('telegram').get_directory('conf').get_directory(cls.class_get_messages_typename())
    
    @_abc.abstractmethod
    def export_data_to_llm(self, specs: _ai_chatbot_data.ChatbotSpecs, images: list[_local_utils_images.Image]) -> _T.Any:
        ...
