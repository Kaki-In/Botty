import os as _os

from .resource_file import ResourceFile

class ResourcesDirectory():
    def __init__(self, path: str) -> None:
        self.__path = _os.path.abspath(path)

        if not _os.path.exists(self.__path):
            _os.makedirs(self.__path)

    @property
    def path(self) -> str:
        return self.__path
    
    def _create_subpath(self, resource_path: str) -> str:
        return self.__path + _os.sep + resource_path
    
    def list_directories(self) -> list[str]:
        return [i for i in _os.listdir(self.__path) if _os.path.isdir(self._create_subpath(i))]
    
    def list_files(self) -> list[str]:
        return [i for i in _os.listdir(self.__path) if _os.path.isfile(self._create_subpath(i))]
    
    def get_directory(self, dirname: str) -> 'ResourcesDirectory':
        return ResourcesDirectory(self._create_subpath(dirname))
    
    def get_resource(self, name: str) -> ResourceFile:
        return ResourceFile(self._create_subpath(name))
    
    def __eq__(self, value: object) -> bool:
        if isinstance(dir:=value, ResourcesDirectory):
            return dir.__path == self.__path
        
        return super().__eq__(value)

