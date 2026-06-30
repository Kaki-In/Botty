import saves as _saves
import typing as _T
import interactions as _interactions

import discord as _discord
import json as _json
import shutil as _shutil
import uuid as _uuid

from .message import DiscordMessageSaver

class _discord_chatbot_discussion_object(_T.TypedDict):
    channel: _discord.TextChannel | _discord.DMChannel
    read: bool
    current_tool_message_id: int | None

class DiscordDiscussionPropertiesSaver():
    def __init__(self, file: _saves.ResourceFile) -> None:
        self.__file = file

    @property
    def exists(self) -> bool:
        return self.__file.exists

    def read_properties(self, client: _T.Optional[_discord.Client] = None) -> _discord_chatbot_discussion_object:
        data = _json.loads(self.__file.read_content())

        channel = None
        if client is not None:
            channel = client.get_channel(data['channel_id'])
            assert channel is not None, f"Channel {data['channel_id']} introuvable dans le cache du client"

        return {
            'channel': channel,             # type: ignore[return-value]
            'read': data['read'],
            'current_tool_message_id': data['current_tool_message_id']
        }
        
    def write_properties(
        self,
        channel: _discord.TextChannel | _discord.DMChannel,
        read: bool,
        current_tool_message_id: int | None
    ) -> None:
        self.__file.write_content(_json.dumps({
            'channel_id': channel.id,
            'guild_id': channel.guild.id if isinstance(channel, _discord.TextChannel) else None,
            'read': read,
            'current_tool_message_id': current_tool_message_id
        }, indent=2))

class DiscordDiscussionSaver():
    def __init__(self, directory: _saves.ResourcesDirectory) -> None:
        self.__directory = directory
        self.__tool_calls_directory = directory.get_directory('tool_calls')
        self.__properties_saver = DiscordDiscussionPropertiesSaver(self.__directory.get_resource('properties.json'))

    @property
    def properties_saver(self) -> DiscordDiscussionPropertiesSaver:
        return self.__properties_saver

    def read_tool_calls(self) -> _T.Sequence[_interactions.ChatCompletionTool.ChatCompletionToolResult]:
        tools: list[_interactions.ChatCompletionTool.ChatCompletionToolResult] = []

        for filename in self.__tool_calls_directory.list_files():
            file = _interactions.ToolCallSaveFile(self.__tool_calls_directory.get_resource(filename))
            tools.append(file.read_tool_call())

        return tools

    def save_tool_call(self, tool_call: _interactions.ChatCompletionTool.ChatCompletionToolResult) -> None:
        file = _interactions.ToolCallSaveFile(self.__tool_calls_directory.get_resource(_uuid.uuid4().hex + '.json'))
        file.write_tool_call(tool_call)

    def get_messages_savers(self) -> _T.Sequence[DiscordMessageSaver]:
        messages: list[tuple[int, DiscordMessageSaver]] = []

        for directory_name in self.__directory.list_directories():
            if directory_name.startswith('dc-message-'):
                saver = DiscordMessageSaver(self.__directory.get_directory(directory_name))
                # On lit uniquement le message_id (pas de client requis) pour le tri.
                message_id = saver.properties_file.read_message_id()
                messages.append((message_id, saver))

        return [saver for _, saver in sorted(messages)]

    def get_message_saver(self, message: _discord.Message) -> DiscordMessageSaver:
        return DiscordMessageSaver(self.__directory.get_directory(
            'dc-message-' + message.created_at.strftime("%d%m%Y-%H%M%S-") + str(message.id)
        ))

    def delete(self) -> None:
        _shutil.rmtree(self.__directory.path)

