import ai.discussion as _ai_discussion

import discord as _discord
import typing as _T

class DiscordChatbotSender(_ai_discussion.ChatbotSender):
    def __init__(self, user: _discord.User | _discord.Member, is_self: bool) -> None:
        super().__init__(str(user.id), is_self)

        self.__user = user

    @property
    def user(self) -> _discord.User | _discord.Member:
        return self.__user

    def to_json(self):
        return {
            'user_id': self.__user.id,
            'username': self.__user.name,
            'display_name': self.__user.display_name,
            'global_name': getattr(self.__user, 'global_name', None),
            'is_self': self.is_self
        }

    @classmethod
    async def from_json(cls, json: dict, client: _discord.Client) -> _T.Self:
        user = await client.fetch_user(json['user_id'])
        return cls(user, json['is_self'])

    def export_to_llm(self):
        return {
            'username': self.__user.display_name,
            'is_you': self.is_self
        }