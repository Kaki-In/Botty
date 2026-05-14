import os as _os

class ResourceFile():
    def __init__(self, path: str):
        self.__path = _os.path.abspath(path)

    @property
    def path(self) -> str:
        return self.__path
    
    @property
    def exists(self) -> bool:
        return _os.path.exists(self.__path)
    
    def delete(self) -> None:
        _os.remove(self.__path)

    def read_content(self) -> str:
        with open(self.__path, 'r') as file:
            return file.read()
        
    def read_raw(self) -> bytes:
        with open(self.__path, 'rb') as file:
            return file.read()
        
    def write_content(self, data: str) -> None:
        with open(self.__path, 'w') as file:
            file.write(data)

    def write_raw(self, data: bytes) -> None:
        with open(self.__path, 'wb') as file:
            file.write(data)

