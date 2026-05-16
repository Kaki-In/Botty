import saves as _saves
import interactions as _interactions
import datetime as _datetime

import json as _json

class ToolCallSaveFile():
    def __init__(self, file: _saves.ResourceFile) -> None:
        self.__file = file
        
    def write_tool_call(self, call: _interactions.ChatCompletionTool.ChatCompletionToolResult) -> None:
        self.__file.write_content(_json.dumps({
            'tool_name': call.tool_name,
            'args': call.args,
            'result': call.result,
            'time': call.time.timestamp()
        }, indent=2))
        
    def read_tool_call(self) -> _interactions.ChatCompletionTool.ChatCompletionToolResult:
        data = _json.loads(self.__file.read_content())
        
        return _interactions.ChatCompletionTool.ChatCompletionToolResult(
            _datetime.datetime.fromtimestamp(data['time'], _datetime.UTC), 
            data['tool_name'],
            data['args'],
            data['result']
        )

