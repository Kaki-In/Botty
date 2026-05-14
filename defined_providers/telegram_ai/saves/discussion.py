import saves as _saves
import typing as _T
import datetime as _datetime

import telegram as _telegram
import json as _json
import shutil as _shutil

from .message import TelegramMessageSaver

class _telegram_chatbot_discussion_object(_T.TypedDict):
    chat: _telegram.Chat
    last_read_time: _datetime.datetime

class TelegramDiscussionPropertiesSaver():
    def __init__(self, file: _saves.ResourceFile) -> None:
        self.__file = file

    @property
    def exists(self) -> bool:
        return self.__file.exists

    def read_properties(self, bot: _T.Optional[_telegram.Bot] = None) -> _telegram_chatbot_discussion_object:
        data = _json.loads(self.__file.read_content())
        return {
            'chat': _telegram.Chat.de_json(data['chat'], bot),
            'last_read_time': _datetime.datetime.fromtimestamp(data['last_read_timestamp'], _datetime.UTC)
        }
    
    def write_properties(self, chat: _telegram.Chat, last_read_time: _datetime.datetime) -> None:
        self.__file.write_content(_json.dumps({
            'chat': chat.to_dict(),
            'last_read_timestamp': last_read_time.timestamp()
        }, indent=2))

class TelegramDiscussionSaver():
    def __init__(self, directory: _saves.ResourcesDirectory) -> None:
        self.__directory = directory

        self.__properties_saver = TelegramDiscussionPropertiesSaver(self.__directory.get_resource('properties.json'))

    @property
    def properties_saver(self) -> TelegramDiscussionPropertiesSaver:
        return self.__properties_saver

    def get_messages_savers(self) -> _T.Sequence[TelegramMessageSaver]:
        messages: list[tuple[int, TelegramMessageSaver]] = []

        for directory_name in self.__directory.list_directories():
            if directory_name.startswith('tg-message-'):
                saver = TelegramMessageSaver(self.__directory.get_directory(directory_name))

                message_id = saver.properties_file.read_message_properties()['telegram_message'].id
                messages.append((message_id, saver))
            
        return [message_saver for time, message_saver in sorted(messages)]
    
    def get_message_saver(self, message: _telegram.Message) -> TelegramMessageSaver:
        saver = TelegramMessageSaver(self.__directory.get_directory('tg-message-' + message.date.strftime("%d%m%Y-%H%M%S-") + str(message.id)))
        return saver
    
    def delete(self) -> None:
        _shutil.rmtree(self.__directory.path)

