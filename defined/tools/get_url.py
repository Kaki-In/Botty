import trafilatura as _trafilatura
import requests as _requests
import saves as _saves
import interactions as _interactions

import typing as _T

class GetUrlTool(_interactions.ChatCompletionTool):
    def __init__(self, name: str="read_url", description: str | None = None, **parameters: _interactions.ChatCompletionTool.Parameter) -> None:
        super().__init__(name, self.read_url, description, 
            href=_interactions.ChatCompletionTool.Parameter(
                {
                    "type": "string",
                    "description": "The raw url hypertext reference to fetch",
                    "pattern": r'^https:\/\/(?:www\.)?[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+(?:\/[^\s]*)?$'
                }
            ),
            options=_interactions.ChatCompletionTool.Parameter(
                {
                    "type": "object",
                    "description": "Options to provide to the URL extraction tool.",
                    "properties": {
                        "output_format": {
                            "type": "string",
                            "enum": ["txt", "markdown", "json", "csv"],
                            "description": "Output format.",
                            "default": "txt"
                        },
                        "include_links": {
                            "type": "boolean",
                            "description": "Preserve links and their target URLs.",
                            "default": False
                        },
                        "include_images": {
                            "type": "boolean",
                            "description": "Include images.",
                            "default": False
                        },
                        "include_tables": {
                            "type": "boolean",
                            "description": "Include tables.",
                            "default": False
                        },
                        "include_formatting": {
                            "type": "boolean",
                            "description": "Preserve text formatting.",
                            "default": False
                        },
                        "with_metadata": {
                            "type": "boolean",
                            "description": "Include page metadata.",
                            "default": False
                        },
                        "favor_precision": {
                            "type": "boolean",
                            "description": "Favor precision over recall.",
                            "default": False
                        },
                        "favor_recall": {
                            "type": "boolean",
                            "description": "Favor recall over precision.",
                            "default": False
                        }
                    },
                    "additionalProperties": False,
                    "required": []
                },
                False
            )
        )
    
    def read_url(self, update_state: _T.Callable[[str], _T.Any], **kwargs) -> str:
        result = _trafilatura.extract(kwargs["href"], **kwargs["options"])
        
        if result is None:
            return "Could not extract"

        return result


