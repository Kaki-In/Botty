from .discord_message import DiscordChatbotMessage

from ..saves import DiscordDiscussionSaver

import interactions as _interactions
import ai.discussion as _ai_discussion, ai.chatbot_data as _ai_chatbot_data

import typing as _T
import discord as _discord
import asyncio as _asyncio
import json as _json
import traceback as _traceback
import saves as _saves

class _discord_discussion_configuration_object(_T.TypedDict):
    public_chats_only_answer_to_mentions: bool

class DiscordChatbotDiscussion(_ai_discussion.ChatbotDiscussion[DiscordChatbotMessage]):
    def __init__(
        self,
        message_methods: _T.Sequence[_T.Type[DiscordChatbotMessage]],
        loop: _asyncio.AbstractEventLoop,
        creators: _interactions.CreatorsMap,
        creators_state: _interactions.CreatorsState,
        client: _discord.Client,
        directory: DiscordDiscussionSaver,
    ) -> None:
        discussion_properties = directory.properties_saver.read_properties(client)

        super().__init__(str(discussion_properties['channel'].id), creators_state)

        self.__channel: _discord.TextChannel | _discord.DMChannel = discussion_properties['channel']
        self.__client = client
        self.__message_methods = message_methods
        self.__loop = loop
        self.__creators = creators
        self.__messages: list[DiscordChatbotMessage] = []

        for message_saver in directory.get_messages_savers():
            message_properties = message_saver.properties_file.read_message_properties(client)

            for message_method in self.__message_methods:
                if message_method.class_get_messages_typename() == message_properties['message_type']:
                    self.__messages.append(message_method.load_back(message_properties['discord_message'], message_saver.message_saves_directory))

        self.__directory = directory

    @property
    def has_unread_messages(self) -> bool:
        return not self.__directory.properties_saver.read_properties()['read']

    @property
    def channel(self) -> _discord.TextChannel | _discord.DMChannel:
        return self.__channel

    @property
    def message_methods(self) -> _T.Sequence[_T.Type[DiscordChatbotMessage]]:
        return self.__message_methods

    @property
    def messages(self) -> _T.Sequence[DiscordChatbotMessage]:
        return self.__messages

    @property
    def tool_calls(self) -> _T.Sequence[_interactions.ChatCompletionTool.ChatCompletionToolResult]:
        return self.__directory.read_tool_calls()

    @property
    def directory(self) -> DiscordDiscussionSaver:
        return self.__directory

    @property
    def current_tool_message(self) -> _discord.Message | None:
        return self.__directory.properties_saver.read_properties()['current_tool_message']

    @current_tool_message.setter
    def current_tool_message(self, message: _discord.Message | None) -> None:
        self.__directory.properties_saver.write_properties(self.__channel, not self.has_unread_messages, message)

    def add_message(self, message: DiscordChatbotMessage) -> None:
        self.__messages.append(message)
        self.save_message(message)
        self.creators_state.interrupt_all()

    def save_message(self, message: DiscordChatbotMessage) -> None:
        message_saver = self.__directory.get_message_saver(message.discord_message)
        message_saver.properties_file.write_message_properties(message.discord_message, message.class_get_messages_typename())

    def insert_message(self, position: int, message: DiscordChatbotMessage) -> None:
        self.__messages.insert(position, message)
        self.save_message(message)
        self.creators_state.interrupt_all()

    def delete_message(self, message: DiscordChatbotMessage) -> None:
        self.__messages.remove(message)
        message_saver = self.__directory.get_message_saver(message.discord_message)
        message_saver.delete()
        self.creators_state.interrupt_all()

    def replace_message_with(self, uuid: str, new_message: DiscordChatbotMessage) -> None:
        for index, message in enumerate(self.messages):
            if message.uuid == uuid:
                self.delete_message(message)
                self.insert_message(index, new_message)
                return

        raise ReferenceError(f"message with uuid {uuid!r} not found")

    def get_message_method_from_discord(self, message: _discord.Message) -> _T.Type[DiscordChatbotMessage]:
        for message_method in self.message_methods:
            if message_method.accepts(message):
                return message_method

        raise TypeError("no method to build this message")

    async def handle_message(self, specs: _ai_chatbot_data.ChatbotSpecs, message: _discord.Message, is_edit: bool = False) -> bool:
        # Pas d'objet Update en Discord : is_edit est passé explicitement
        # depuis les handlers on_message / on_message_edit.
        try:
            message_method = self.get_message_method_from_discord(message)
        except TypeError:
            try:
                await message.delete()
            except Exception:
                print("Could not handle message", message)
            return False

        config = _saves.ConfigurationFile[_discord_discussion_configuration_object](
            specs.directory.get_directory('discord').get_directory('conf').get_resource('discussions.json'),
            {'public_chats_only_answer_to_mentions': True}
        ).read_configuration()

        if not isinstance(message.channel, _discord.DMChannel) and config['public_chats_only_answer_to_mentions'] and not message_method.is_for_me(message):
            return False

        message_saver = self.__directory.get_message_saver(message)
        message_saver.properties_file.write_message_properties(message, message_method.class_get_messages_typename())

        created_message = await message_method.create_from_discord(message, specs, self.__creators, self.creators_state, message_saver.message_saves_directory)

        if is_edit:
            self.replace_message_with(str(message.id), created_message)
        else:
            self.add_message(created_message)

        self.save_message(created_message)
        self.mark_as_unread()

        return True

    def get_json_schema(self) -> _T.Any:
        return {
            'oneOf': [
                {
                    'type': 'object',
                    'properties': {
                        'type': {
                            'type': 'string',
                            'const': message_method.class_get_messages_typename()
                        },
                        'data': message_method.class_get_json_schema(),
                    },
                    'required': ['type', 'data'],
                    'additionalProperties': False
                }
                for message_method in self.message_methods
            ]
        }

    def get_json_description_for_llm(self) -> str:
        a = (
            "The messages structure are an object containing the following keys :\n"
            '- "type" : the type of the message to send \n'
            '- "data" : the data of the message (depending the message type)\n\n'
            "You can reply by a message from any of these types:\n"
        )

        for message_method in self.message_methods:
            a += f"- {message_method.class_get_messages_typename()}: \n{message_method.class_get_json_description_for_llm()}\n\n"

        a += 'You can also include a message identifier to reply to if needed, under the key "replying_to_old_message".'

        return a

    def add_message_from_llm_response(self, specs: _ai_chatbot_data.ChatbotSpecs, response: str) -> None:
        self.current_tool_message = None

        data = _json.loads(response)
        assert isinstance(data, dict)

        for method in self.message_methods:
            if method.class_get_messages_typename() == data['type']:
                reply_to = data.get('replying_to_old_message')

                if len(self.messages) > 0 and reply_to == self.messages[-1].replies_to and self.messages[-1].is_from_self:
                    reply_to = None

                discord_message, extras = _asyncio.run_coroutine_threadsafe(
                    method.load_from_llm(self.__channel, specs, self.__creators, self.creators_state, data['data'], reply_to),
                    self.__loop
                ).result()

                message_saver = self.__directory.get_message_saver(discord_message)
                message_saver.properties_file.write_message_properties(discord_message, method.class_get_messages_typename())

                try:
                    message = _asyncio.run_coroutine_threadsafe(
                        method.create_with_extras(discord_message, specs, extras, message_saver.message_saves_directory),
                        self.__loop
                    ).result()
                except Exception:
                    _traceback.print_exc()
                    message_saver.delete()
                    raise

                self.add_message(message)

    def get_context_prompt(self, specs: _ai_chatbot_data.ChatbotSpecs) -> str:
        private_context = specs.directory.get_directory("discord").get_directory('conf').get_resource('private_prompt.txt')
        if not private_context.exists:
            private_context.write_content('You are speaking in a private discussion with {distant_username}. \nYour username is {local_username} and your full name is {local_full_name}.')

        guild_context = specs.directory.get_directory("discord").get_directory('conf').get_resource('guild_prompt.txt')
        if not guild_context.exists:
            guild_context.write_content(
                'You are speaking in a public channel named "{discussion_name}" on the server "{guild_name}", '
                'containing {members_count} members.\n'
                'You should stay quiet most of the time.\n'
                'Your username is {local_username} and your full name is {local_full_name}.'
            )

        bot_user = self.__client.user
        assert bot_user is not None

        if isinstance(self.__channel, _discord.DMChannel):
            return private_context.read_content().format(
                distant_username=self.__channel.recipient.name if self.__channel.recipient else "a single distant user",
                local_username=bot_user.name,
                local_full_name=bot_user.display_name,
            )
        else:
            # guild.member_count est mis en cache par discord.py, pas besoin d'async
            return guild_context.read_content().format(
                discussion_name=self.__channel.name,
                guild_name=self.__channel.guild.name,
                members_count=self.__channel.guild.member_count,
                local_username=bot_user.name,
                local_full_name=bot_user.display_name,
            )

    def mark_as_unread(self) -> None:
        self.__directory.properties_saver.write_properties(self.__channel, False, self.current_tool_message)

    def mark_as_read(self) -> None:
        self.__directory.properties_saver.write_properties(self.__channel, True, self.current_tool_message)

    def on_tool_started(self, tool: _interactions.ChatCompletionTool, args: _T.Mapping[str, _T.Any]) -> None:
        _asyncio.run_coroutine_threadsafe(self.prepare_tool_message(tool, args), self.__loop).result()

    def on_tool_update(self, tool: _interactions.ChatCompletionTool, args: _T.Mapping[str, _T.Any], event_data: str) -> None:
        _asyncio.run_coroutine_threadsafe(self.update_tool_message(tool, args, event_data), self.__loop).result()

    def on_tool_finished(self, tool: _interactions.ChatCompletionTool, result: _interactions.ChatCompletionTool.ChatCompletionToolResult) -> None:
        _asyncio.run_coroutine_threadsafe(self.remove_tool_message(tool, result), self.__loop).result()

    async def prepare_tool_message(self, tool: _interactions.ChatCompletionTool, args: _T.Mapping[str, _T.Any]) -> None:
        message = await self.__channel.send(f"_Calling tool {_discord.utils.escape_markdown(tool.name)}..._")
        self.current_tool_message = message

    async def update_tool_message(self, tool: _interactions.ChatCompletionTool, args: _T.Mapping[str, _T.Any], event_data: str) -> None:
        if self.current_tool_message is None:
            await self.prepare_tool_message(tool, args)

        current_message = self.current_tool_message
        assert current_message is not None

        await current_message.edit(content=f"_Calling tool {_discord.utils.escape_markdown(tool.name)}...\n{_discord.utils.escape_markdown(event_data)}_")

    async def remove_tool_message(self, tool: _interactions.ChatCompletionTool, result: _interactions.ChatCompletionTool.ChatCompletionToolResult) -> None:
        self.__directory.save_tool_call(result)

        if self.current_tool_message is None:
            await self.prepare_tool_message(tool, result.args)

        current_message = self.current_tool_message
        assert current_message is not None

        await current_message.edit(content=f"_{_discord.utils.escape_markdown(tool.name)} action ended:\n{_discord.utils.escape_markdown(result.result)}_")