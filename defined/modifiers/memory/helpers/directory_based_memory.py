from ..base import *

import typing as _T
import abc as _abc
import saves as _saves
import datetime as _datetime
import json as _json

class _chatbot_directory_based_memory_file_object(_T.TypedDict):
    sentence: str
    context: _T.Mapping[str, _T.Any]
    date: float

class _chatbot_directory_based_memory_configuration_object(_T.TypedDict):
    lost_after_days: int

class ChatbotDirectoryBasedMemory(ChatbotMemory, _abc.ABC):
    def __init__(self, name: str, directory: _saves.ResourcesDirectory) -> None:
        ChatbotMemory.__init__(self, name)
        
        self.__directory = directory

    def save_remembering(self, remembering: ChatbotMemory.Remembering) -> None:
        resource = self.__directory.get_resource(str(remembering.uuid) + '.remembering')
        resource.write_content(_json.dumps({
            'date': remembering.date.timestamp(),
            'context': remembering.context,
            'sentence': remembering.data
        }))
        
    def forget_remembering(self, remembering: ChatbotMemory.Remembering) -> None:
        self.__directory.get_resource(str(remembering.uuid) + '.remembering').delete()

    def get_all_rememberings(self) -> _T.Sequence[ChatbotMemory.Remembering]:
        rememberings: list[ChatbotMemory.Remembering] = []
        
        for filename in self.__directory.list_files():
            if filename.endswith('.remembering') and not filename.startswith('.'):
                resource = self.__directory.get_resource(filename)
                data: _chatbot_directory_based_memory_file_object = _json.loads(resource.read_content())
                
                rememberings.append(ChatbotMemory.Remembering(data['sentence'], data['context'], _datetime.datetime.fromtimestamp(data['date'])))
        
        return rememberings

    def clear(self) -> None:
        for filename in self.__directory.list_files():
            self.__directory.get_resource(filename).delete()

    @property
    def remembering_losing_time(self) -> _datetime.timedelta:
        days_count = _saves.ConfigurationFile[_chatbot_directory_based_memory_configuration_object](self.__directory.get_resource('settings.json'), {
            'lost_after_days': 30
        }).read_configuration()['lost_after_days']
        
        return _datetime.timedelta(days=days_count)



