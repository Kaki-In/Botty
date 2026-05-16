from .bot_handler import TelegramBotHandler
from ..objects import TelegramChatbotMessage

import interactions as _interactions
import ai.chatbot_data as _ai_chatbot_data
import ai.discussion as _ai_discussion
import typing as _T

class MainTelegramBotsHandler(_ai_discussion.ChatbotDiscussionsProvider):
    def __init__(self, *message_methods: _T.Type[TelegramChatbotMessage]) -> None:
        self.__message_methods = list(message_methods)
        self.__creator_facts: list[tuple[_interactions.CreatorFactory, _T.Type, _T.Type]] = []

        self.__bots: list[TelegramBotHandler] = []
    
    def add_message_method(self, method: _T.Type[TelegramChatbotMessage]) -> None:
        self.__message_methods.append(method)

    @property
    def message_methods(self) -> _T.Sequence[_T.Type[TelegramChatbotMessage]]:
        return self.__message_methods

    def add_creator_factory[iobj, oobj](self, factory: _interactions.CreatorFactory[iobj, oobj], input_type: _T.Type[iobj], output_type: _T.Type[oobj]) -> None:
        self.__creator_facts.append((factory, input_type, output_type))

    @property
    def creator_factories(self) -> _T.Sequence[_interactions.CreatorFactory]:
        return [factory for factory, itype, otype in self.__creator_facts]
    
    def _create_creators_map(self) -> _interactions.CreatorsMap:
        map = _interactions.CreatorsMap()

        for factory, itype, otype in self.__creator_facts:
            map.add_creator_factory(factory, itype, otype)
        
        return map

    def get_bot_handler(self, specs: _ai_chatbot_data.ChatbotSpecs) -> TelegramBotHandler:
        for bot in self.__bots:
            if bot.chatbot_specs == specs:
                return bot
        
        new_bot = TelegramBotHandler(specs, self._create_creators_map(), _interactions.CreatorsState(), self.__message_methods)
        self.__bots.append(new_bot)
        return new_bot

    def load_all_discussions(self, specs: _ai_chatbot_data.ChatbotSpecs) -> _T.Sequence[_ai_discussion.ChatbotDiscussion]:
        return self.get_bot_handler(specs).load_all_discussions()
    
    def stop_all_bots(self, should_wait: bool=False) -> None:
        for bot in self.__bots:
            bot.stop(should_wait)


