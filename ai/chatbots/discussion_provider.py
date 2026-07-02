import abc as _abc
import typing as _T
import queue as _queue

from ..discussion.discussion import ChatbotDiscussion
from .message_processor import ChatbotMessage

from ..chatbot_data import ChatbotSpecs

class ChatbotDiscussionsProvider[discussion: ChatbotDiscussion, message: ChatbotMessage](_abc.ABC):
    def __init__(self) -> None:
        super().__init__()
        
        self.__new_messages_queues: dict[str, _queue.Queue[tuple[message, discussion]]] = {}
        
    def _get_new_messages_queues(self, specs: ChatbotSpecs) -> _queue.Queue[tuple[message, discussion]]:
        if not specs.name in self.__new_messages_queues:
            self.__new_messages_queues[specs.name] = _queue.Queue()
        
        return self.__new_messages_queues[specs.name]
    
    def has_next_added_messages(self, specs: ChatbotSpecs) -> bool:
        if not specs.name in self.__new_messages_queues:
            return False
        
        return not self.__new_messages_queues[specs.name].empty()
        
    def next_added_message(self, specs: ChatbotSpecs) -> tuple[ChatbotMessage, ChatbotDiscussion[ChatbotMessage]]:
        if not specs.name in self.__new_messages_queues:
            self.__new_messages_queues[specs.name] = _queue.Queue()
        
        return self.__new_messages_queues[specs.name].get()
    
    @_abc.abstractmethod
    def load_all_discussions(self, specs: ChatbotSpecs) -> _T.Sequence[ChatbotDiscussion]:
        ...
    
