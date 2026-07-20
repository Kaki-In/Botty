from ai.chatbot_data.chatbot_specs import ChatbotSpecs
from ai.discussion.discussion import ChatbotDiscussion

from ..base import *

import typing as _T
import abc as _abc
import saves as _saves
import datetime as _datetime
import json as _json
import interactions as _interactions

import ai.discussion as _ai_discussion
import ai.chatbot_data as _ai_chatbot_data

class _chatbot_directory_based_memory_file_object(_T.TypedDict):
    sentence: str
    context: _T.Mapping[str, _T.Any]
    date: float

class _chatbot_directory_based_memory_configuration_object(_T.TypedDict):
    top_k: int
    threshold: float
    lost_after_days: int

class ChatbotDirectoryMemory[preparation_type](ChatbotMemory[preparation_type]):
    class Evaluator[evaluator_preparation_type](_abc.ABC):
        @_abc.abstractmethod
        def relevancy(self, state: _interactions.CreatorsState, preparation: evaluator_preparation_type, memory_name: str, remembering: ChatbotMemory.Remembering, discussion: _ai_discussion.ChatbotDiscussion, specs: _ai_chatbot_data.ChatbotSpecs) -> float:
            ...
    
    def __init__(self, name: str, description: str, evaluator: Evaluator[preparation_type], directory: _saves.ResourcesDirectory) -> None:
        super().__init__(name, description)
        
        self.__directory = directory
        self.__evaluator = evaluator
        self.__configuration = _saves.ConfigurationFile[_chatbot_directory_based_memory_configuration_object](self.__directory.get_resource('settings.json'), {
            'top_k': -1,
            'threshold': 0.5,
            'lost_after_days': 30
        })
        
    @property
    def directory(self) -> _saves.ResourcesDirectory:
        return self.__directory
    
    @property
    def evaluator(self) -> Evaluator[preparation_type]:
        return self.__evaluator
    
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

    def delete_useless_elements(self) -> None:
        days_count = self.__configuration.read_configuration()['lost_after_days']
        
        max_time = _datetime.timedelta(days=days_count)
        
        for remembering in self.get_all_rememberings()[:] :
            if _datetime.datetime.now() - remembering.date > max_time:
                self.forget_remembering(remembering)
                continue

    def get_linked_rememberings(self, state: _interactions.CreatorsState, preparation: preparation_type, discussion: ChatbotDiscussion, specs: ChatbotSpecs) -> _T.Sequence[ChatbotMemory.Remembering]:
        rememberings: list[tuple[float, ChatbotMemory.Remembering]] = []
        
        configuration = self.__configuration.read_configuration()
        
        for remembering in self.get_all_rememberings():
            rememberings.append((self.__evaluator.relevancy(state, preparation, self.name, remembering, discussion, specs), remembering))
        
        rememberings.sort(key = lambda r: r[0])
            
        return [r[1] for r in rememberings if r[0] > configuration['threshold']][:configuration['top_k']]



