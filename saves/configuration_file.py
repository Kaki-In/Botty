from .resource_file import ResourceFile

import json as _json

class ConfigurationFile[ConfigurationContent]():
    def __init__(self, file: ResourceFile, default_data: ConfigurationContent):
        self.__file = file

        if not file.exists:
            file.write_content(_json.dumps(default_data, indent=2))
    
    def read_configuration(self) -> ConfigurationContent:
        return _json.loads(self.__file.read_content())

