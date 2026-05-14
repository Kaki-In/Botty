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
import saves as _saves
import math as _math
import datetime as _datetime
import random as _random

class _realistic_chatbot_configuration_object(_T.TypedDict):
    min_waiting_seconds: float
    max_waiting_seconds: float
    complete_cold_state_count: int
    min_relaunch_after_minutes: int
    relaunch_after_prob: float

class RealisticChatbot(Chatbot):
    def __init__(self, name: str, specs: ChatbotSpecs) -> None:
        super().__init__(name, specs)

        self.__prompt = self.specs.directory.get_resource("prompt.txt")
        if not self.__prompt.exists:
            self.__prompt.write_content("You are a helpful assistant")

        self.__first_message_prompt = self.specs.directory.get_resource("first_prompt.txt")
        if not self.__first_message_prompt.exists:
            self.__first_message_prompt.write_content("You must simply greet them !")

        self.__on_case_relaunch = self.specs.directory.get_resource('relaunch_prompt.txt')
        if not self.__on_case_relaunch.exists:
            self.__on_case_relaunch.write_content("The distant user did not respond anything yet. You can restart the discussion, or simple not answer anything by an empty json list []. ")

        self.__configuration = _saves.ConfigurationFile[_realistic_chatbot_configuration_object](self.specs.directory.get_resource('config.json'), {
            'min_waiting_seconds': 1,
            'max_waiting_seconds': 60,
            'complete_cold_state_count': 10,
            'min_relaunch_after_minutes': 1440,
            'relaunch_after_prob': 0.01
        })

    def answer_to_discussion(self, discussion: ChatbotDiscussion, force: bool = False) -> None:
        print(self.name, "answering to", discussion)

        json_schema = discussion.get_json_schema()

        if json_schema in ('str', None):
            final_json_schema = {
                'type': 'array',
                'items': {
                    'type': 'string'
                },
                'description': 'a json list of all messages to send. You should use distinct messages separating your ideas.'
            }
            llm_json_schema = final_json_schema
        else:
            final_json_schema = {
                'type': 'array',
                'items': json_schema,
                'description': 'a json list of all messages to send. You should use distinct messages separating your ideas.'
            }

            llm_json_schema = {
                'type': 'array',
                'items': discussion.get_json_schema_for_llm(),
                'description': 'a json list of all messages to send. You should use distinct messages separating your ideas.'
            }

        if force:
            final_json_schema['minItems'] = 1

        messages = [
            ChatCompletionMessage('system', "\n\n---\n\n".join((self.__prompt.read_content(), discussion.get_context_prompt(self.specs), "You must respect the following JSON Schema:\n" + _json.dumps(llm_json_schema))))
        ]

        for grouped_messages in discussion.grouped_sender_messages:
            images: list[_local_utils_images.Image] = []
            
            message_exports = [message.export_to_llm(self.specs, images) for message in grouped_messages]

            if json_schema in ('str', None):
                message_content = "\n\n".join(message_exports)
            else:
                message_content = _json.dumps(message_exports)
            
            messages.append(ChatCompletionMessage('assistant' if grouped_messages[0].is_from_self else 'user', message_content, images))
        
        if messages[-1].role == 'assistant':
            messages.append(ChatCompletionMessage('system', self.__on_case_relaunch.read_content()))

        if len(discussion.messages) == 0:
            messages.append(ChatCompletionMessage('system', self.__first_message_prompt.read_content()))
        
        result_messages = _json.loads(self.complete(ChatCompletionDescription(messages, final_json_schema), discussion))

        for message in result_messages:
            if not json_schema in ('str', None):
                message = _json.dumps(message)

            discussion.add_message_from_llm_response(self.specs, message)

        if len(result_messages) == 0:
            print(self.name, "did not answer anything")

    def calculate_wait_time(self, coeff: int) -> float:
        configuration = self.__configuration.read_configuration()

        return configuration['max_waiting_seconds'] - (configuration['max_waiting_seconds'] - configuration['min_waiting_seconds']) * _math.exp(-5 * coeff / configuration['complete_cold_state_count']) # 5 because 1 - exp(-5) > 99%

    def run(self) -> None:
        wait_time_coeff = 0

        while not self.should_stop:
            discussions = self.discussions

            found_discussion: bool = False

            for discussion in discussions:
                last_message_time = discussion.last_message_time

                configuration = self.__configuration.read_configuration()

                if last_message_time is None or discussion.last_read_time < last_message_time \
                    or ((_datetime.datetime.now(_datetime.UTC) - last_message_time > _datetime.timedelta(minutes=configuration['min_relaunch_after_minutes']) and _random.random() < configuration['relaunch_after_prob'])):
                    found_discussion = True
                    try:
                        self.answer_to_discussion(discussion, len(discussion.messages)>0 and not discussion.messages[-1].is_from_self)
                        discussion.mark_as_read_now()
                    except InteractionInterruptionError:
                        pass
                    except Exception:
                        traceback.print_exc()
            
            if found_discussion:
                wait_time_coeff /= 2
            else:
                wait_time_coeff += 1

            t = _time.monotonic()
            
            while _time.monotonic() - t < wait_time_coeff and not self.should_stop:
                _time.sleep(0.1)




