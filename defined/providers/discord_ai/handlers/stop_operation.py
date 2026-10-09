import typing as _typing

import ai.chatbots as _ai_chatbots, ai.chatbot_data as _ai_chatbot_data, ai.discussion as _ai_discussion

from .bot_handler import DiscordBotHandler
from ..objects.discord_discussion import DiscordChatbotDiscussion

class DiscordStopOperation(_ai_chatbots.ChatbotOperation):
    def __init__(self, bots_list: list[DiscordBotHandler]):
        super().__init__("stop", "Efface la discussion en cours")
        
        self.__bots = bots_list
        
    def get_bot_handler(self, name: str) -> DiscordBotHandler | None:
        for bot in self.__bots:
            if bot.chatbot_specs.name ==  name:
                return bot

    def _proceed(self, specs: _ai_chatbot_data.ChatbotSpecs, discussion: _ai_discussion.ChatbotDiscussion, **values: _typing.Any) -> str:
        assert isinstance(discussion, DiscordChatbotDiscussion)
        
        bot_handler = self.get_bot_handler(specs.name)
        
        if bot_handler is None:
            raise ValueError("This bot does not handle any discussion")
        
        bot_handler.delete_discussion(discussion)
        
        return "Les messages ont été supprimés du répertoire du bot"

