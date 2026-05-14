from .message import ChatbotMessage

from ai.chatbot_data import ChatbotSpecs
from interactions import CreatorsState

import typing as _T
import datetime as _datetime
import abc as _abc

class ChatbotDiscussion[messagesTypes: ChatbotMessage](_abc.ABC):
    def __init__(self, uuid: str, creators_state: CreatorsState, last_read_time: _T.Optional[_datetime.datetime] = None) -> None:
        super().__init__()

        self.__uuid = uuid
        self.__last_read = last_read_time or _datetime.datetime.fromtimestamp(0, _datetime.UTC)
        self.__creators_state = creators_state

    @property
    def uuid(self) -> str:
        return self.__uuid

    @property
    @_abc.abstractmethod
    def messages(self) -> _T.Sequence[messagesTypes]:
        ...

    @property
    def creators_state(self) -> CreatorsState:
        return self.__creators_state

    @property
    def last_read_time(self) -> _datetime.datetime:
        return self.__last_read
    
    @last_read_time.setter
    def last_read_time(self, time: _datetime.datetime) -> None:
        self.__last_read = time

    def mark_as_read_now(self) -> None:
        self.__last_read = _datetime.datetime.now(_datetime.UTC)
    
    @property
    def last_message_time(self) -> _datetime.datetime | None:
        if not len(self.messages):
            return None
        
        return self.messages[-1].time

    @_abc.abstractmethod
    def add_message(self, message: messagesTypes) -> None:
        ...

    @_abc.abstractmethod
    def insert_message(self, position: int, message: messagesTypes) -> None:
        ...

    @_abc.abstractmethod
    def delete_message(self, message: messagesTypes) -> None:
        ...

    @_abc.abstractmethod
    def replace_message_with(self, uuid: str, new_message: messagesTypes) -> None:
        ...
    
    def get_message(self, uuid: str) -> messagesTypes:
        for message in self.messages:
            if message.uuid == uuid:
                return message
        
        raise ReferenceError(f"message with uuid {uuid!r} not found")
    
    @_abc.abstractmethod
    def get_json_schema(self) -> _T.Any:
        ...
    
    @_abc.abstractmethod
    def get_json_schema_for_llm(self) -> _T.Any:
        ...
    
    @_abc.abstractmethod
    def add_message_from_llm_response(self, specs: ChatbotSpecs, response: str) -> None:
        ...

    @property
    def grouped_sender_messages(self) -> _T.Sequence[_T.Sequence[ChatbotMessage]]:
        messages: list[list[ChatbotMessage]] = []

        for message in self.messages:
            if len(messages) == 0 or message.is_from_self != messages[-1][-1].is_from_self:
                messages.append([message])

            else:
                messages[-1].append(message)

        return messages
    
    @_abc.abstractmethod
    def get_context_prompt(self, specs: ChatbotSpecs) -> str:
        ...
    


