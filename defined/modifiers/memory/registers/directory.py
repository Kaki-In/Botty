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

class ChatbotDirectoryMemoryRegistry(ChatbotMemoryRegistry, _abc.ABC):
    def __init__(self, directory: _saves.ResourcesDirectory) -> None:
        super().__init__()
        
        self.__directory = directory

    def save_remembering(self, remembering: ChatbotMemoryRegistry.Remembering) -> None:
        resource = self.__directory.get_resource(str(remembering.uuid) + '.remembering')
        resource.write_content(_json.dumps({
            'date': remembering.date.timestamp(),
            'context': remembering.context,
            'sentence': remembering.data
        }))
        
    def forget_remembering(self, remembering: ChatbotMemoryRegistry.Remembering) -> None:
        self.__directory.get_resource(str(remembering.uuid) + '.remembering').delete()

    def get_all_rememberings(self) -> _T.Sequence[ChatbotMemoryRegistry.Remembering]:
        rememberings: list[ChatbotMemoryRegistry.Remembering] = []
        
        for filename in self.__directory.list_files():
            if filename.endswith('.remembering') and not filename.startswith('.'):
                resource = self.__directory.get_resource(filename)
                data: _chatbot_directory_based_memory_file_object = _json.loads(resource.read_content())
                
                rememberings.append(ChatbotMemoryRegistry.Remembering(data['sentence'], data['context'], _datetime.datetime.fromtimestamp(data['date'])))
        
        return rememberings

    def clear(self) -> None:
        for filename in self.__directory.list_files():
            self.__directory.get_resource(filename).delete()

    def delete_useless_elements(self) -> None:
        days_count = _saves.ConfigurationFile[_chatbot_directory_based_memory_configuration_object](self.__directory.get_resource('settings.json'), {
            'lost_after_days': 30
        }).read_configuration()['lost_after_days']
        
        max_time = _datetime.timedelta(days=days_count)
        
        for remembering in self.get_all_rememberings()[:] :
            if _datetime.datetime.now() - remembering.date > max_time:
                self.forget_remembering(remembering)
                continue
            




