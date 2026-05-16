import abc as _abc
import typing as _T
import datetime as _datetime
import local_utils.images as _local_utils_images

from .sender import ChatbotSender
from ..chatbot_data import ChatbotSpecs

class ChatbotMessage[senderType: ChatbotSender](_abc.ABC):
    _cls_name: str

    def __init_subclass__(cls, name: _T.Optional[str] = None) -> None:
        super().__init_subclass__()

        if name is None:
            if getattr(cls, '__abstractmethods__', None) is not None:
                raise TypeError(f"{cls.__name__} must provide a 'name' argument")
            return

        cls._cls_name = name

    @classmethod
    def class_get_messages_typename(cls) -> str:
        return cls._cls_name
    
    def __init__(self, uuid: str, time: _datetime.datetime, sender: senderType) -> None:
        super().__init__()

        self.__uuid = uuid
        self.__time = time
        self.__chatbot_sender = sender

    @property
    def uuid(self) -> str:
        return self.__uuid

    @property
    def time(self) -> _datetime.datetime:
        return self.__time
    
    @property
    def sender(self) -> senderType:
        return self.__chatbot_sender
    
    @property
    def is_from_self(self) -> bool:
        return self.__chatbot_sender.is_self
    
    @_abc.abstractmethod
    def export_to_llm(self, specs: ChatbotSpecs, images: list[_local_utils_images.Image]) -> _T.Any:
        ...


