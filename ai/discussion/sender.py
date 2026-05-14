import abc as _abc
import typing as _T

class ChatbotSender(_abc.ABC):
    _subclasses = {}
    _defined_elements = {}

    def __init__(self, uuid: str, is_self: bool) -> None:
        super().__init__()

        self.__uuid = uuid
        self.__is_self = is_self

    @property
    def uuid(self) -> str:
        return self.__uuid

    @property
    def is_self(self) -> bool:
        return self.__is_self
    
    @_abc.abstractmethod
    def export_to_llm(self) -> _T.Any:
        ...


