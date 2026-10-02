import trafilatura as _trafilatura
import requests as _requests
import saves as _saves
import interactions as _interactions

import typing as _T
import urllib.robotparser as _url_robot_parser
import urllib.parse as _url_parser

class _get_url_tool_configuration_object(_T.TypedDict):
    user_agent: str
    enable_robots_refusal: bool

class GetUrlTool(_interactions.ChatCompletionTool):
    def __init__(self, configuration_directory: _saves.ResourcesDirectory, name: str="read_url", description: str | None = None, **parameters: _interactions.ChatCompletionTool.Parameter) -> None:
        super().__init__(name, self.read_url, description, 
            href=_interactions.ChatCompletionTool.Parameter(
                {
                    "type": "string",
                    "description": "The raw url hypertext reference to fetch",
                    "pattern": "^https://[a-zA-Z0-9._~:/?#@!$&'()*+,;=%-]+$"
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
        
        self.__configuration_file = _saves.ConfigurationFile[_get_url_tool_configuration_object](configuration_directory.get_resource("config.json"), {
            'user_agent': "botty (1.0) - https://github.com/Kaki-In/Botty",
            'enable_robots_refusal': True
        })
    
    def read_url(self, update_state: _T.Callable[[str], _T.Any], **kwargs) -> tuple[str, str]:
        configuration = self.__configuration_file.read_configuration()
        
        url = kwargs["href"]
        
        parsed = _url_parser.urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

        rp = _url_robot_parser.RobotFileParser(robots_url)
        rp.read()
        
        if configuration['enable_robots_refusal'] and not rp.can_fetch(configuration["user_agent"], url):
            return "Fetch refused due to robots.txt policy", "Fetch refused due to robots.txt policy"
        
        html = _requests.get(kwargs["href"], headers={
            "User-Agent": configuration["user_agent"],
        }).text
        
        result = _trafilatura.extract(html, **kwargs.get("options", {}))
        
        if result is None:
            return "Could not extract", "Error during extraction"

        return result, f"Page {url} fetched succesfully"


