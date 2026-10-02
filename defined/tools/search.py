import interactions as _interactions
import typing as _T
import datetime as _datetime
import json as _json

class SearchResult:
    def __init__(self, title: str, body: str, href: str, date: _datetime.datetime) -> None:
        self.__title = title
        self.__body = body
        self.__href = href
        self.__date = date
    
    @property
    def title(self) -> str:
        return self.__title
    
    @property
    def body(self) -> str:
        return self.__body
    
    @property
    def href(self) -> str:
        return self.__href
    
    @property
    def date(self) -> _datetime.datetime:
        return self.__date
    
    def to_json(self) -> _T.Any:
        return {
            'title': self.__title,
            'body': self.__body,
            'href': self.__href,
            'date': self.__date.strftime("%d/%m/%Y, %H:%M:%S")
        }

class SearchTool(_interactions.ChatCompletionTool):
    def __init__(self,
                 name: str,
                 description: str | None = None,
                 **searchers: _T.Callable[[str], _T.Sequence[SearchResult]]
        ) -> None:
        super().__init__(name, self.operate_search, description, 
            search = _interactions.ChatCompletionTool.Parameter({
                'type': 'string',
                'description': "a simple search request"
            }),
            engine = _interactions.ChatCompletionTool.Parameter({
                'type': 'string',
                'description': "the search engine to use",
                'enum': list(searchers.keys())
            })
        )
        
        self.__searchers = searchers
    
    def operate_search(self, update_state: _T.Callable[[str], _T.Any], **kwargs) -> str: 
        engine = kwargs['engine']
        results = self.__searchers[engine](kwargs["search"])
        
        return _json.dumps([
            result.to_json()
            for result in results
        ])


