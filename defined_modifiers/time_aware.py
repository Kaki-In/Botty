from ai.chatbot_data import ChatbotSpecs
from ai.chatbots import ChatbotDiscussionModifier
from ai.discussion import ChatbotDiscussion

from defined_creators.used_objects import ChatCompletionDescription, ChatCompletionMessage

import typing as _T
import saves as _saves
import datetime as _datetime
import babel.dates as _babel_dates

class _time_aware_configuration_object(_T.TypedDict):
    format: str
    utc: tuple[int, int] | None
    locale: str
    intro_text: str

class TimeAwareChatbotModifier(ChatbotDiscussionModifier):
    def get_configuration_from(self, specs: ChatbotSpecs) -> _time_aware_configuration_object:
        return _saves.ConfigurationFile[_time_aware_configuration_object](specs.configuration_directory.get_directory('time_aware').get_resource('conf.json'), {
                'format': "%A %d %B %Y à %Hh%M",
                "utc": None,
                "locale": "en_US.utf-8",
                "intro_text": "Current time and date are : "
            }).read_configuration()
    
    def format_datetime(self, datetime: _datetime.datetime, configuration: _time_aware_configuration_object) -> str:
        hours, minutes = configuration.get('utc') or [0, 0]
        utc = _datetime.timezone(_datetime.timedelta(hours=hours, minutes=minutes))

        return _babel_dates.format_datetime(datetime, configuration['format'], utc, configuration['locale'])

    def modify_chat_completion(self, specs: ChatbotSpecs, discussion: ChatbotDiscussion, description: ChatCompletionDescription) -> ChatCompletionDescription:
        configuration = self.get_configuration_from(specs)

        if description.messages and description.messages[-1].role == 'system':
            return description.removing_messages(count_after=1).adding_message_after(
                ChatCompletionMessage('system', description.messages[-1].content+"\n\n"+configuration['intro_text']+self.format_datetime(_datetime.datetime.now(), configuration), description.messages[-1].images)
            )
        else:
            return description.adding_message_after(
                ChatCompletionMessage('system', configuration['intro_text']+self.format_datetime(_datetime.datetime.now(), configuration))
            )




