import ai.chatbot_data as _ai_chatbot_data
import ai.discussion as _ai_discussion

from ..base import ChatbotMemoriesPreparator, ChatbotMemoryFactory

import interactions as _interactions
import typing as _T

class ChatbotMemoryQueryBasedPreparator(ChatbotMemoriesPreparator[str]):
    def __init__(self, examinator: _interactions.CreatorFactory[tuple[_ai_chatbot_data.ChatbotSpecs,_ai_discussion.ChatbotDiscussion, _T.Any], str], **memory_factories: tuple[ChatbotMemoryFactory[str], str]) -> None:
        super().__init__(**memory_factories)
        
        self.__examinator = examinator
        
    @property
    def examinator(self) -> _interactions.CreatorFactory[tuple[_ai_chatbot_data.ChatbotSpecs,_ai_discussion.ChatbotDiscussion, _T.Any], str]:
        return self.__examinator

    def _prepare_remembering(self, creators_state: _interactions.CreatorsState, discussion: _ai_discussion.ChatbotDiscussion, specs: _ai_chatbot_data.ChatbotSpecs) -> str:
        return creators_state.create_from_factory(self.__examinator, (specs, discussion,
            {
                'type': 'string'
            }
        ), specs.configuration_directory.get_directory('memory_query_preparator'))


