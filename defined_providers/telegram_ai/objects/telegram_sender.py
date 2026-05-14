from ai.discussion import ChatbotSender

import telegram as _telegram
import typing as _T

class TelegramChatbotSender(ChatbotSender):
    def __init__(self, user: _telegram.User, is_self: bool) -> None:
        super().__init__(str(user.id), is_self)

        self.__user = user

    @property
    def user(self) -> _telegram.User:
        return self.__user
    
    def to_json(self):
        return {
            'user': self.__user.to_dict(),
            'is_self': self.is_self
        }
    
    @classmethod
    def from_json(cls, json, bot: _telegram.Bot) -> _T.Self:
        return cls(_telegram.User.de_json(json['user'], bot), json['is_self'])
    
    def export_to_llm(self):
        return {
            'user_id': self.__user.id,
            'username': self.__user.full_name,
            'language_code': self.__user.language_code,
            'is_you': self.is_self
        }

