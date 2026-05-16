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
    @_abc.abstractmethod
    def has_unread_messages(self) -> bool:
        ...
    
    @_abc.abstractmethod
    def mark_as_read(self) -> None:
        ...
        
    @_abc.abstractmethod
    def add_message(self, message: messagesTypes) -> None:
        ...
        
    @_abc.abstractmethod
    def on_tool_started(self, tool: _interactions.ChatCompletionTool, args: _T.Mapping[str, _T.Any]) -> None:
        ...
        
    @_abc.abstractmethod
    def on_tool_update(self, tool: _interactions.ChatCompletionTool, args: _T.Mapping[str, _T.Any], event_data: str) -> None:
        ...
    
    @_abc.abstractmethod
    def on_tool_finished(self, tool: _interactions.ChatCompletionTool, result: _interactions.ChatCompletionTool.ChatCompletionToolResult) -> None:
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
            if not isinstance(message, ChatbotMessage):
                continue
            
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
        messages: list[list] = []

        last_message_sender = None
        for message in self.messages:
            message_sender = message.is_from_self
            
            if last_message_sender != message_sender:
                messages.append([message])
                last_message_sender = message_sender

            else:
                messages[-1].append(message)

        return messages
    
    @_abc.abstractmethod
    def get_context_prompt(self, specs: ChatbotSpecs) -> str:
        ...
    


