from .resource_file import ResourceFile

import json as _json

class ConfigurationFile[ConfigurationContent]():
    def __init__(self, file: ResourceFile, default_data: ConfigurationContent):
        self.__file = file

        if not file.exists:
            self.overwrite_with(default_data)
    
    def read_configuration(self) -> ConfigurationContent:
        return _json.loads(self.__file.read_content())
    
    def overwrite_with(self, data: ConfigurationContent) -> None:
        self.__file.write_content(_json.dumps(data, indent=2))

