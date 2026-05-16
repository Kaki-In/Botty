import typing as _T
import saves as _saves
import json as _json
import telegram as _telegram
import shutil as _shutil

class _telegram_properties_file_object(_T.TypedDict):
    telegram_message: _telegram.Message
    message_type: str
    read: bool

class TelegramMessagePropertiesFile():
    def __init__(self, resource: _saves.ResourceFile) -> None:
        self.__resource = resource

    def read_message_properties(self, bot: _T.Optional[_telegram.Bot] = None) -> _telegram_properties_file_object:
        data = _json.loads(self.__resource.read_content())
        return {
            'telegram_message': _telegram.Message.de_json(data['telegram_data'], bot),
            'message_type': data['message_type'],
            'read': data['read']
        }
    
    def write_message_properties(self, message: _telegram.Message, message_type: str, read: bool) -> None:
        self.__resource.write_content(_json.dumps({
            'telegram_data': message.to_dict(),
            'message_type': message_type,
            'read': read
        }, indent=2))

class TelegramMessageSaver():
    def __init__(self, directory: _saves.ResourcesDirectory) -> None:
        self.__directory = directory
        self.__properties_file = TelegramMessagePropertiesFile(directory.get_resource('properties.json'))
        self.__saves_directory = directory.get_directory('saves')

    @property
    def directory(self) -> _saves.ResourcesDirectory:
        return self.__directory
    
    @property
    def message_saves_directory(self) -> _saves.ResourcesDirectory:
        return self.__saves_directory
    
    @property
    def properties_file(self) -> TelegramMessagePropertiesFile:
        return self.__properties_file
    
    def delete(self) -> None:
        _shutil.rmtree(self.__directory.path)


