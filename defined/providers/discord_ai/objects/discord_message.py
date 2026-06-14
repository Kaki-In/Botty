from .discord_sender import DiscordChatbotSender

import interactions as _interactions
import ai.discussion as _ai_discussion, ai.chatbot_data as _ai_chatbot_data

import abc as _abc
import discord as _discord
import typing as _T
import local_utils.images as _local_utils_images
import saves as _saves
import datetime as _datetime

class _discord_messages_configuration_object(_T.TypedDict):
    utc: tuple[int, int] | list[int]

class DiscordChatbotMessage(_ai_discussion.ChatbotMessage[DiscordChatbotSender], _abc.ABC):
    @classmethod
    @_abc.abstractmethod
    def class_get_description(cls) -> str:
        ...

    @classmethod
    @_abc.abstractmethod
    def accepts(cls, message: _discord.Message) -> bool:
        ...

    @classmethod
    def is_for_me(cls, message: _discord.Message) -> bool:
        if isinstance(message.channel, _discord.DMChannel):
            return True

        bot_member = message.guild.me if message.guild else None
        if not bot_member:
            return False

        if (
            message.reference
            and message.reference.resolved
            and isinstance(message.reference.resolved, _discord.Message)
            and message.reference.resolved.author.id == bot_member.id
        ):
            return True

        if any(u.id == bot_member.id for u in message.mentions):
            return True

        return False

    @classmethod
    @_abc.abstractmethod
    def class_get_json_schema(cls) -> _T.Any:
        ...

    @classmethod
    @_abc.abstractmethod
    def class_get_json_description_for_llm(cls) -> str:
        ...

    @classmethod
    @_abc.abstractmethod
    async def load_from_llm(cls, channel: _discord.TextChannel | _discord.DMChannel, specs: _ai_chatbot_data.ChatbotSpecs, creators: _interactions.CreatorsMap, creators_state: _interactions.CreatorsState, data, answer_to: _T.Optional[int] = None,
    ) -> tuple[_discord.Message, _T.Any]:
        ...

    @classmethod
    async def create_with_extras(cls, message: _discord.Message, specs: _ai_chatbot_data.ChatbotSpecs, extras, directory: _saves.ResourcesDirectory,
    ) -> _T.Self:
        return cls(message, directory)

    @classmethod
    async def create_from_discord(cls, message: _discord.Message, specs: _ai_chatbot_data.ChatbotSpecs, creators: _interactions.CreatorsMap, creators_state: _interactions.CreatorsState, directory: _saves.ResourcesDirectory,
    ) -> _T.Self:
        return cls(message, directory)

    @classmethod
    def load_back(cls, message: _discord.Message, directory: _saves.ResourcesDirectory) -> _T.Self:
        return cls(message, directory)

    def __init__(self, message: _discord.Message, directory: _saves.ResourcesDirectory) -> None:
        bot_member = message.guild.me if message.guild else None
        is_bot = bot_member is not None and message.author.id == bot_member.id

        sender = DiscordChatbotSender(message.author, is_bot)

        super().__init__(str(message.id), message.created_at, sender)

        self.__message = message
        self.__directory = directory

    @property
    def discord_message(self) -> _discord.Message:
        return self.__message

    @property
    def _directory(self) -> _saves.ResourcesDirectory:
        return self.__directory

    @property
    def replies_to(self) -> int | None:
        if self.__message.reference is None:
            return None

        return self.__message.reference.message_id

    def export_to_llm(self, specs: _ai_chatbot_data.ChatbotSpecs, images: list[_local_utils_images.Image]) -> _T.Any:
        config = _saves.ConfigurationFile[_discord_messages_configuration_object](
            specs.directory.get_directory('discord').get_directory('conf').get_resource('messages.json'),
            {'utc': [0, 0]}
        ).read_configuration()

        data = {
            'message_id': self.discord_message.id,
            'type': self.class_get_messages_typename(),
            'data': self.export_data_to_llm(specs, images),
            'sender': self.sender.export_to_llm(),
            'date': self.time.astimezone(
                _datetime.timezone(_datetime.timedelta(hours=config['utc'][0], minutes=config['utc'][1]))
            ).strftime("%A %d/%m/%Y, %H:%M"),
        }

        if self.__message.reference is not None:
            data['replying_to_message'] = self.__message.reference.message_id

        if not isinstance(self.__message.channel, _discord.DMChannel):
            data['is_especially_for_me'] = self.is_for_me(self.__message)

        return data

    @classmethod
    def get_bot_discord_configuration(cls, specs: _ai_chatbot_data.ChatbotSpecs) -> _saves.ResourcesDirectory:
        return specs.directory.get_directory('discord').get_directory('conf').get_directory(cls.class_get_messages_typename())

    @_abc.abstractmethod
    def export_data_to_llm(self, specs: _ai_chatbot_data.ChatbotSpecs, images: list[_local_utils_images.Image]) -> _T.Any:
        ...