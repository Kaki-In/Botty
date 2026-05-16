from .message import ChatbotMessage

from ..chatbot_data import ChatbotSpecs

import interactions as _interactions

import typing as _T
import abc as _abc

class ChatbotDiscussion[messagesTypes: ChatbotMessage](_abc.ABC):
    def __init__(self, uuid: str, creators_state: _interactions.CreatorsState) -> None:
        super().__init__()

        self.__uuid = uuid
        self.__creators_state = creators_state

    @property
    def uuid(self) -> str:
        return self.__uuid

    @property
    @_abc.abstractmethod
    def messages(self) -> _T.Sequence[messagesTypes]:
        ...

    @property
    def creators_state(self) -> _interactions.CreatorsState:
        return self.__creators_state

    @property
    def has_unread_messages(self) -> bool:
        for message in self.messages:
            if not message.has_been_read:
                return True
            
        return False
    
    def mark_as_read(self) -> None:
        for message in self.messages:
            message.mark_as_read()
    
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
    


