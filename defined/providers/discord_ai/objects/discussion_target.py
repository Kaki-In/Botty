import discord as _discord

class DiscordDiscussionTarget():
    def __init__(self, target: _discord.TextChannel | tuple[_discord.User, _discord.DMChannel]) -> None:
        self.__target = target
        
    @property
    def target(self) -> _discord.TextChannel | tuple[_discord.User, _discord.DMChannel]:
        return self.__target
    
    @property
    def descriptor(self) -> _discord.TextChannel | _discord.User:
        return self.__target if isinstance(self.__target, _discord.TextChannel) else self.__target[0]

    @property
    def channel(self) -> _discord.TextChannel | _discord.DMChannel:
        return self.__target if isinstance(self.__target, _discord.TextChannel) else self.__target[1]
    
    @property
    def is_private(self) -> bool:
        return isinstance(self.channel, _discord.DMChannel)
