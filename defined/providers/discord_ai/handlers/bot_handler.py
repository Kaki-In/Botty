import discord as _discord
import typing as _T
import asyncio as _asyncio
import traceback as _traceback
import threading as _threading

from ..objects import DiscordChatbotDiscussion, DiscordChatbotMessage, DiscordDiscussionTarget
from ..saves import DiscordBotSaver, DiscordDiscussionSaver

import interactions as _interactions
import queue as _queue
import ai.discussion as _ai_discussion, ai.chatbot_data as _ai_chatbot_data


class DiscordBotHandler():
    def __init__(self, created_messages_queue: _queue.Queue[tuple[DiscordChatbotMessage, DiscordChatbotDiscussion]], specs: _ai_chatbot_data.ChatbotSpecs, creators_map: _interactions.CreatorsMap, message_methods: _T.Sequence[_T.Type[DiscordChatbotMessage]], directly_start: bool = True) -> None:
        discord_directory = specs.directory.get_directory('discord')
        token_file = discord_directory.get_resource('token')
        
        if not (token_file.exists and (token := token_file.read_content().replace(" ", '').replace("\n", '')) != ''):
            token_file.write_content('')
            raise ValueError("Please provide a token in file " + repr(token_file.path))
        
        self.__created_messages_queue = created_messages_queue

        self.__token = token
        self.__directory = DiscordBotSaver(discord_directory.get_directory('discussions'))
        self.__creators_map = creators_map
        self.__message_methods = list(message_methods)
        self.__chatbot_specs = specs
        self.__loop = _asyncio.new_event_loop()

        self.__states: dict[int, _interactions.CreatorsState] = {}

        intents = _discord.Intents.default()
        intents.message_content = True
        intents.members = True
        self.__client = _discord.Client(intents=intents)

        self.__tree = _discord.app_commands.CommandTree(self.__client)
        
        @self.__tree.command(name="forget", description="Efface la discussion")
        async def cmd_forget(interaction: _discord.Interaction):
            channel = interaction.channel
            
            if not isinstance(channel, (_discord.TextChannel, _discord.DMChannel)):
                await interaction.response.send_message("Commande non supportée ici.", ephemeral=True)
                return
            
            if isinstance(channel, _discord.DMChannel):
                assert isinstance(interaction.user, _discord.User)
                target = DiscordDiscussionTarget((interaction.user, channel))
            else:
                target = DiscordDiscussionTarget(channel)

            discussion = self.get_discussion_or_create(target)
            self.delete_discussion(discussion)
            await interaction.response.send_message("Discussion oubliée.", ephemeral=True)
                
        self.__thread = _threading.Thread(target=self.__run)

        self.__client.event(self.on_ready)
        self.__client.event(self.on_message)
        self.__client.event(self.on_message_edit)

        if directly_start:
            self.start()

    def get_state_for_discussion(self, discussion_id: int) -> _interactions.CreatorsState:
        if not discussion_id in self.__states:
            self.__states[discussion_id] = _interactions.CreatorsState()
            
        return self.__states[discussion_id]

    @property
    def chatbot_specs(self) -> _ai_chatbot_data.ChatbotSpecs:
        return self.__chatbot_specs

    @property
    def interactors_map(self) -> _interactions.CreatorsMap:
        return self.__creators_map

    @property
    def message_methods(self) -> _T.Sequence[_T.Type[DiscordChatbotMessage]]:
        return self.__message_methods

    @property
    def client(self) -> _discord.Client:
        return self.__client

    def start(self) -> None:
        self.__thread.start()

    def __run(self) -> None:
        _asyncio.set_event_loop(self.__loop)
        self.__loop.run_until_complete(self.__client.start(self.__token))
        self.__loop.run_forever()

    def stop(self, join: bool = False):
        _asyncio.ensure_future(self.__client.close(), loop=self.__loop)
        self.__loop.call_soon_threadsafe(self.__loop.stop)
        
        for state in self.__states.values():
            state.interrupt_all()

        if join:
            try:
                self.__thread.join()
            except Exception:
                pass

    def _get_discussion_saver(self, target: DiscordDiscussionTarget) -> DiscordDiscussionSaver:
        return self.__directory.get_discussion_saver(target.descriptor)

    def get_discussion_or_create(self, target: DiscordDiscussionTarget) -> DiscordChatbotDiscussion:
        saver = self._get_discussion_saver(target)

        if not saver.properties_saver.exists:
            saver.properties_saver.write_properties(target.descriptor.id, target.is_private,  False, None)

        return DiscordChatbotDiscussion(self.__created_messages_queue, self.__message_methods, self.__loop, self.__creators_map, self.get_state_for_discussion(target.channel.id), self.__client, saver, target)

    def delete_discussion(self, discussion: DiscordChatbotDiscussion) -> None:
        saver = self._get_discussion_saver(discussion.target)
        saver.delete()
        discussion.creators_state.interrupt_all()
        
    async def on_ready(self):
        assert self.__client.user
        
        await self.__tree.sync()
        await self.__client.user.edit(username=self.__client.user.name)
        print(f'Logged in as {self.__client.user}')
        
    async def on_message(self, message: _discord.Message):
        assert self.__client.user
        
        if message.author == self.__client.user:
            return

        channel = message.channel
        
        if not isinstance(channel, (_discord.TextChannel, _discord.DMChannel)):
            return
        
        if isinstance(channel, _discord.DMChannel):
            assert isinstance(message.author, _discord.User)
            target = (message.author, channel)
        else:
            target = channel

        try:
            discussion = self.get_discussion_or_create(DiscordDiscussionTarget(target))
            await discussion.handle_message(self.__chatbot_specs, message)
            
        except Exception:
            _traceback.print_exc()
            print("Could not handle message", message)

    async def on_message_edit(self, before: _discord.Message, after: _discord.Message):
        await self.on_message(after)
        
    async def _get_discord_target(self, channel_or_user_id: int, private: bool) -> DiscordDiscussionTarget:
        channel = self.__client.get_channel(channel_or_user_id)
        
        if isinstance(channel, _discord.TextChannel):
            return DiscordDiscussionTarget(channel)

        if private:
            user = await self.__client.fetch_user(channel_or_user_id)
            
            dm_channel = user.dm_channel or await user.create_dm()
        
            return DiscordDiscussionTarget((user, dm_channel))
        else:
            channel = await self.__client.fetch_channel(channel_or_user_id)
            
            assert isinstance(channel, _discord.TextChannel)
            
            return DiscordDiscussionTarget(channel)
    
    def load_all_discussions(self) -> _T.Sequence[_ai_discussion.ChatbotDiscussion]:
        discussions: list[DiscordChatbotDiscussion] = []

        if not self.__client.is_ready():
            return []

        for discussion_saver in self.__directory.discussions_savers:
            properties = discussion_saver.properties_saver.read_properties()
            
            try:
                future = _asyncio.run_coroutine_threadsafe(
                    self._get_discord_target(properties['target_id'], properties['is_private']),
                    self.__loop,
                )
                target = future.result()
                    
                discussion = DiscordChatbotDiscussion(
                    self.__created_messages_queue,
                    self.__message_methods,
                    self.__loop,
                    self.__creators_map,
                    self.get_state_for_discussion(target.channel.id),
                    self.__client,
                    discussion_saver,
                    target
                )
            except Exception as exc:
                print("Could not get channel from", properties, ":", repr(exc))
                continue

            if len(discussion.messages) > 0:
                discussions.append(discussion)

        return discussions

