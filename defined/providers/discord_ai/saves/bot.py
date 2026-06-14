import saves as _saves
import typing as _T
import discord as _discord

from .discussion import DiscordDiscussionSaver

class DiscordBotSaver():
    def __init__(self, directory: _saves.ResourcesDirectory) -> None:
        self.__directory = directory

    @property
    def discussions_savers(self) -> _T.Sequence[DiscordDiscussionSaver]:
        discussions: list[DiscordDiscussionSaver] = []

        for directory_name in self.__directory.list_directories():
            if directory_name.startswith("dc-discussion-"):
                discussions.append(DiscordDiscussionSaver(self.__directory.get_directory(directory_name)))

        return discussions

    def get_discussion_saver(self, channel: _discord.TextChannel | _discord.DMChannel) -> DiscordDiscussionSaver:
        return DiscordDiscussionSaver(self.__directory.get_directory('dc-discussion-' + str(channel.id)))