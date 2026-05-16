from .chatbot import Chatbot
from ..discussion import ChatbotDiscussionModifier, ChatbotDiscussionsProvider

import typing as _T

class ChatbotsRegistry():
    def __init__(self) -> None:
        self.__chatbots: list[Chatbot] = []

    def add_chatbot(self, chatbot: Chatbot) -> None:
        self.__chatbots.append(chatbot)

    def remove_chatbot(self, chatbot: Chatbot) -> None:
        self.__chatbots.remove(chatbot)

    def add_modifier_to_chatbots(self, modifier: ChatbotDiscussionModifier) -> None:
        for chatbot in self.__chatbots:
            chatbot.add_discussion_modifier(modifier)

    def add_provider_to_chatbots(self, provider: ChatbotDiscussionsProvider) -> None:
        for chatbot in self.__chatbots:
            chatbot.add_discussion_provider(provider)

    def start_all_chatbots(self) -> None:
        for chatbot in self.__chatbots:
            chatbot.start()

    def stop_all_chatbots(self) -> None:
        for chatbot in self.__chatbots:
            chatbot.stop()

    @property
    def chatbots(self) -> _T.Sequence[Chatbot]:
        return self.__chatbots
    
    def get_chatbot_by_name(self, name: str) -> Chatbot:
        for chatbot in self.__chatbots:
            if chatbot.name == name:
                return chatbot
        
        raise ReferenceError("chatbot not found: " + repr(name))
    
    def __iter__(self) -> _T.Iterable[Chatbot]:
        return iter(self.__chatbots.copy())


