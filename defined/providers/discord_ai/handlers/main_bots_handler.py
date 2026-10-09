from .bot_handler import DiscordBotHandler
from .stop_operation import DiscordStopOperation
from ..objects import DiscordChatbotMessage, DiscordChatbotDiscussion

import interactions as _interactions
import ai.chatbot_data as _ai_chatbot_data
import ai.chatbots as _ai_chatbots
import ai.discussion as _ai_discussion
import typing as _T

class MainDiscordBotsHandler(_ai_chatbots.ChatbotDiscussionsProvider[DiscordChatbotDiscussion, DiscordChatbotMessage]):
    def __init__(self, *message_methods: _T.Type[DiscordChatbotMessage]) -> None:
        self.__bots: list[DiscordBotHandler] = []
        super().__init__(DiscordStopOperation(self.__bots))
        
        self.__message_methods = list(message_methods)
        self.__creators_map = _interactions.CreatorsMap()
        
    def add_message_method(self, method: _T.Type[DiscordChatbotMessage]) -> None:
        self.__message_methods.append(method)

    @property
    def message_methods(self) -> _T.Sequence[_T.Type[DiscordChatbotMessage]]:
        return self.__message_methods

    def add_creator_factory[iobj, oobj](self, factory: _interactions.CreatorFactory[iobj, oobj], input_type: _T.Type[iobj], output_type: _T.Type[oobj]) -> None:
        self.__creators_map.add_creator_factory(factory, input_type, output_type)

    def get_bot_handler(self, specs: _ai_chatbot_data.ChatbotSpecs) -> DiscordBotHandler:
        for bot in self.__bots:
            if bot.chatbot_specs == specs:
                return bot

        new_bot = DiscordBotHandler(self._get_new_messages_queues(specs), specs, self.__creators_map, self.__message_methods)
        self.__bots.append(new_bot)
        return new_bot

    def load_all_discussions(self, specs: _ai_chatbot_data.ChatbotSpecs) -> _T.Sequence[_ai_discussion.ChatbotDiscussion]:
        try:
            return self.get_bot_handler(specs).load_all_discussions()
        except:
            return []

    def update_operations(self, specs: _ai_chatbot_data.ChatbotSpecs, operations: _T.Sequence[_ai_chatbots.ChatbotOperation]) -> None:
        try:
            bot = self.get_bot_handler(specs)
        except:
            return
        
        bot._set_operations(operations)

    def stop_all_bots(self, should_wait: bool = False) -> None:
        for bot in self.__bots:
            bot.stop(should_wait)

