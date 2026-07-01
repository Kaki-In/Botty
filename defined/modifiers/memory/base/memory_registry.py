import abc as _abc
import typing as _T
import datetime as _datetime
import uuid as _uuid

# _cmrcfmps = _T.ParamSpec('_cmrcfmps')

class ChatbotMemoryRegistry(_abc.ABC):
    class Remembering():
        def __init__(self, data: str, context: _T.Mapping[str, _T.Any], date: _datetime.datetime, uuid: _T.Optional[_uuid.UUID] = None) -> None:
            self.__data = data
            self.__context = context
            self.__date = date
            self.__uuid = uuid or _uuid.uuid4()
            
        @property
        def data(self) -> str:
            return self.__data
        
        @property
        def context(self) -> _T.Mapping[str, _T.Any]:
            return self.__context
        
        @property
        def date(self) -> _datetime.datetime:
            return self.__date
        
        @property
        def uuid(self) -> _uuid.UUID:
            return self.__uuid
        
        def __repr__(self) -> str:
            return ""\
                f"# {self.__date.strftime("%d/%m/%Y, %H:%M:%S")} : {self.__data}\n"\
                f"Context :\n{self.__context}"
    
    def __init__(self) -> None:
        self.save_remembering = self._checks_for_memory(self.save_remembering)
        self.forget_remembering = self._checks_for_memory(self.forget_remembering)
        self.get_all_rememberings = self._checks_for_memory(self.get_all_rememberings)
        self.clear = self._checks_for_memory(self.clear)
                
    def _checks_for_memory[**funcargs, rtype](self, func: _T.Callable[funcargs, rtype]) -> _T.Callable[funcargs, rtype]:
        def fn(*args: funcargs.args, **kwargs: funcargs.kwargs):
            self.delete_useless_elements()
                
            return func(*args, **kwargs)

        return fn
    
    @_abc.abstractmethod
    def delete_useless_elements(self) -> None:
        ...
    
    @_abc.abstractmethod
    def save_remembering(self, remembering: Remembering) -> None:
        ...
        
    @_abc.abstractmethod
    def forget_remembering(self, remembering: Remembering) -> None:
        ...
        
    @_abc.abstractmethod
    def get_all_rememberings(self) -> _T.Sequence[Remembering]:
        ...
    
    @_abc.abstractmethod
    def clear(self) -> None:
        ...

