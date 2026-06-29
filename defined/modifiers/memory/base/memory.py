import abc as _abc
import typing as _T
import datetime as _datetime
import uuid as _uuid

class ChatbotMemory(_abc.ABC):
    
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
    
    def __init__(self, name: str) -> None:
        super().__init__()
        
        self.__name = name
        
    @property
    def name(self) -> str:
        return self.__name
    
    @property
    @_abc.abstractmethod
    def remembering_losing_time(self) -> _datetime.timedelta:
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
    
    def remember_from(self, query: str) -> _T.Sequence[Remembering]:
        relevant_rememberings: list[ChatbotMemory.Remembering] = []
        
        for remembering in self.get_all_rememberings()[:] :
            if _datetime.datetime.now() - remembering.date > self.remembering_losing_time:
                self.forget_remembering(remembering)
                continue
            
            if self.is_relevant(query, remembering):
                relevant_rememberings.append(remembering)
                
        return relevant_rememberings
    
    @_abc.abstractmethod
    def is_relevant(self, query: str, remembering: Remembering) -> bool:
        ...

    @_abc.abstractmethod
    def clear(self) -> None:
        ...

