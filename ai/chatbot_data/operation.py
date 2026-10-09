import typing as _T
import enum as _enum
import abc as _abc

from ..discussion import ChatbotDiscussion
from . import ChatbotSpecs

class ChatbotOperation(_abc.ABC):
    class Argument:
        class Type(_enum.IntEnum):
            INT = 0
            FLOAT = 1
            BOOL = 2
            STRING = 3
            DATE = 4
            DURATION = 5
        
        def __init__(self, name: str, type: 'Type', mandatory: bool=True) -> None:
            self.__name = name
            self.__type = type
            self.__mandatory = mandatory
        
        @property
        def name(self) -> str:
            return self.__name
        
        @property
        def type(self) -> 'Type':
            return self.__type
        
        @property
        def is_mandatory(self) -> bool:
            return self.__mandatory

        @is_mandatory.setter
        def is_mandatory(self, enabled: bool) -> None:
            self.__mandatory = enabled
    
    def __init__(self, name: str, description: str, **arguments: 'Argument.Type') -> None:
        super().__init__()
        
        self.__name = name
        self.__description = description
        self.__arguments = [ChatbotOperation.Argument(argument_name, argument_type) for argument_name, argument_type in arguments.items()]
    
    @property
    def name(self) -> str:
        return self.__name
    
    @property
    def description(self) -> str:
        return self.__description
    
    @property
    def arguments(self) -> _T.Mapping[str, 'Argument']:
        return {
            argument.name: argument
            for argument in self.__arguments
        }
    
    @property
    def mandatory_arguments(self) -> _T.Mapping[str, 'Argument']:
        return {
            argument.name: argument
            for argument in self.__arguments
            if argument.is_mandatory
        }
    
    @property
    def optional_arguments(self) -> _T.Mapping[str, 'Argument']:
        return {
            argument.name: argument
            for argument in self.__arguments
            if not argument.is_mandatory
        }
    
    def get_argument_by_name(self, name: str) -> 'Argument':
        for argument in self.__arguments:
            if argument.name == name:
                return argument
        
        raise KeyError(name)
    
    def __ensure_dict(self, d: _T.Mapping[str, _T.Any]) -> None:
        if not set(self.mandatory_arguments.keys()).issubset(d.keys()):
            raise ValueError("missing mandatory arguments")

        if not set(d.keys()).issubset(self.arguments.keys()):
            raise ValueError("unknown additional arguments provided")
        
    def __call__(self, specs: ChatbotSpecs, discussion: ChatbotDiscussion, **values: _T.Any) -> str:
        self.__ensure_dict(values)
        
        return self._proceed(specs, discussion, **values)

    @_abc.abstractmethod
    def _proceed(self, specs: ChatbotSpecs, discussion: ChatbotDiscussion, **values: _T.Any) -> str:
        ...


