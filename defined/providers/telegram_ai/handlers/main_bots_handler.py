from .bot_handler import TelegramBotHandler
from ..objects import TelegramChatbotMessage

import interactions as _interactions
import ai.chatbot_data as _ai_chatbot_data
import ai.discussion as _ai_discussion
import ai.chatbots as _ai_chatbots
import typing as _T

class MainTelegramBotsHandler(_ai_chatbots.ChatbotDiscussionsProvider):
    def __init__(self, *message_methods: _T.Type[TelegramChatbotMessage]) -> None:
        super().__init__()
        
        self.__message_methods = list(message_methods)
        self.__creators_map = _interactions.CreatorsMap()

        self.__bots: list[TelegramBotHandler] = []
    
    def add_message_method(self, method: _T.Type[TelegramChatbotMessage]) -> None:
        self.__message_methods.append(method)

    @property
    def message_methods(self) -> _T.Sequence[_T.Type[TelegramChatbotMessage]]:
        return self.__message_methods

    def add_creator_factory[iobj, oobj](self, factory: _interactions.CreatorFactory[iobj, oobj], input_type: _T.Type[iobj], output_type: _T.Type[oobj]) -> None:
        self.__creators_map.add_creator_factory(factory, input_type, output_type)

    def get_bot_handler(self, specs: _ai_chatbot_data.ChatbotSpecs) -> TelegramBotHandler:
        for bot in self.__bots:
            if bot.chatbot_specs == specs:
                return bot
        
        new_bot = TelegramBotHandler(self._get_new_messages_queues(specs), specs, self.__creators_map, self.__message_methods)
        self.__bots.append(new_bot)
        return new_bot

    def load_all_discussions(self, specs: _ai_chatbot_data.ChatbotSpecs) -> _T.Sequence[_ai_discussion.ChatbotDiscussion]:
        try:
            return self.get_bot_handler(specs).load_all_discussions()
        except:
            return []
    
    def stop_all_bots(self, should_wait: bool=False) -> None:
        for bot in self.__bots:
            bot.stop(should_wait)

    def update_operations(self, specs: _ai_chatbot_data.ChatbotSpecs, operations: _T.Sequence[_ai_chatbots.ChatbotOperation]) -> None:
        ... # not compatible yet



