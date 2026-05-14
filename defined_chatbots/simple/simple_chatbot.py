from ai.chatbots import Chatbot
from ai.chatbot_data import ChatbotSpecs
from ai.discussion import ChatbotDiscussion

from interactions import InteractionInterruptionError
from defined_creators.used_objects import ChatCompletionDescription, ChatCompletionMessage

import typing as _T
import json as _json
import local_utils.images as _local_utils_images
import traceback
import time as _time

class SimpleChatbot(Chatbot):
    def __init__(self, name: str, specs: ChatbotSpecs) -> None:
        super().__init__(name, specs)

        self.__prompt = self.specs.directory.get_resource("prompt.txt")

        if not self.__prompt.exists:
            self.__prompt.write_content("You are a helpful assistant")

    def answer_to_discussion(self, discussion: ChatbotDiscussion) -> None:
        json_schema = discussion.get_json_schema()

        messages = [
            ChatCompletionMessage('system', self.__prompt.read_content() + ('' if json_schema in ('str', None) else "\n\nYou must respect the following JSON Schema:\n" + _json.dumps(json_schema)))
        ]

        for message in discussion.messages:
            images: list[_local_utils_images.Image] = []
            
            message_content = message.export_to_llm(self.specs, images)
            if not isinstance(message_content, str):
                message_content = _json.dumps(message_content)

            messages.append(ChatCompletionMessage('assistant' if message.sender.is_self else 'user', message_content, images))
        
        result_message = self.complete(ChatCompletionDescription(messages, json_schema), discussion)

        discussion.add_message_from_llm_response(self.specs, result_message)

    def run(self) -> None:
        while not self.should_stop:
            discussions = self.discussions

            for discussion in discussions:
                last_message_time = discussion.last_message_time

                if last_message_time is None or discussion.last_read_time < last_message_time:
                    try:
                        self.answer_to_discussion(discussion)
                        discussion.mark_as_read_now()
                    except InteractionInterruptionError:
                        pass
                    except Exception:
                        traceback.print_exc()
            
            _time.sleep(10)




