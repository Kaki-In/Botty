import ai.chatbot_data as _ai_chatbot_data
import ai.chatbots as _ai_chatbots
import ai.discussion as _ai_discussion

import interactions as _interactions
import typing as _T
import saves as _saves
import datetime as _datetime
import babel.dates as _babel_dates

class _time_aware_configuration_object(_T.TypedDict):
    format: str
    utc: tuple[int, int] | None
    locale: str
    intro_text: str

class TimeAwareChatbotModifier(_ai_discussion.ChatbotDiscussionModifier):
    def get_configuration_from(self, specs: _ai_chatbot_data.ChatbotSpecs) -> _time_aware_configuration_object:
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

    def modify_chat_completion(self, specs: _ai_chatbot_data.ChatbotSpecs, discussion: _ai_discussion.ChatbotDiscussion, description: _interactions.ChatCompletionDescription) -> _interactions.ChatCompletionDescription:
        configuration = self.get_configuration_from(specs)
        
        if description.messages and isinstance(last_message:=description.messages[-1], _interactions.ChatCompletionMessage) and last_message.role == 'system':
                return description.removing_messages(count_after=1).adding_message_after(
                    _interactions.ChatCompletionMessage('system', last_message.content+"\n\n"+configuration['intro_text']+self.format_datetime(_datetime.datetime.now(), configuration), last_message.images)
                )

        return description.adding_message_after(
            _interactions.ChatCompletionMessage('system', configuration['intro_text']+self.format_datetime(_datetime.datetime.now(), configuration))
        )




