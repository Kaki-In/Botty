import discord as _discord
import discord.ext.tasks as _discord_ext_tasks
import typing as _T
import asyncio as _asyncio
import traceback as _traceback
import threading as _threading
import datetime as _datetime
import inspect as _inspect
import traceback as _traceback

from ..objects import DiscordChatbotDiscussion, DiscordChatbotMessage, DiscordDiscussionTarget
from ..saves import DiscordBotSaver, DiscordDiscussionSaver

import interactions as _interactions
import queue as _queue
import ai.discussion as _ai_discussion, ai.chatbot_data as _ai_chatbot_data, ai.chatbots as _ai_chatbots


PY_TYPES = {
    _ai_chatbots.ChatbotOperation.Argument.Type.INT: int, _ai_chatbots.ChatbotOperation.Argument.Type.FLOAT: float, _ai_chatbots.ChatbotOperation.Argument.Type.BOOL: bool,
    _ai_chatbots.ChatbotOperation.Argument.Type.STRING: str, _ai_chatbots.ChatbotOperation.Argument.Type.DATE: str, _ai_chatbots.ChatbotOperation.Argument.Type.DURATION: str,
}
CONVERTERS = {
    _ai_chatbots.ChatbotOperation.Argument.Type.DATE: _datetime.date.fromisoformat,
    _ai_chatbots.ChatbotOperation.Argument.Type.DURATION: lambda s: _datetime.timedelta(seconds=float(s))
}


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
        self.__operations: _T.Sequence[_ai_chatbots.ChatbotOperation] = ()
        
        self.__thread = _threading.Thread(target=self.__run)

        self.__client.event(self.on_ready)
        self.__client.event(self.on_message)
        self.__client.event(self.on_message_edit)
        
        self.__last_tree_state: _T.Any = None

        if directly_start:
            self.start()
    
    def build_command(self, operation: _ai_chatbots.ChatbotOperation) -> _discord.app_commands.Command:
        args = sorted(operation.arguments.values(), key=lambda a: not a.is_mandatory)  # obligatoires d'abord

        async def callback(interaction: _discord.Interaction, **kwargs):
            values = {
                name: CONVERTERS[operation.get_argument_by_name(name).type](v)
                    if operation.get_argument_by_name(name).type in CONVERTERS else v
                for name, v in kwargs.items() if v is not None
            }
            await interaction.response.defer()

            channel = interaction.channel
            
            if not isinstance(channel, (_discord.TextChannel, _discord.DMChannel)):
                await interaction.followup.send("Commande non supportée ici.", ephemeral=True)
                return
            
            if isinstance(channel, _discord.DMChannel):
                assert isinstance(interaction.user, _discord.User)
                target = DiscordDiscussionTarget((interaction.user, channel))
            else:
                target = DiscordDiscussionTarget(channel)

            discussion = self.get_discussion_or_create(target)
            
            result = await _asyncio.to_thread(operation._proceed, self.__chatbot_specs, discussion, **values)
            
            try:
                await interaction.followup.send(embed = _discord.Embed(
                    title=f"Opération effectuée",
                    description=result[:2000],
                    color=_discord.Color.green()
                ))
            
            except Exception as exc:
                await interaction.followup.send(embed = _discord.Embed(
                    title=f"Une erreur s'est produite",
                    description=str(exc),
                    color=_discord.Color.green(),
                ))
            

        params = [_inspect.Parameter("interaction", _inspect.Parameter.POSITIONAL_OR_KEYWORD,
                                    annotation=_discord.Interaction)]
        for a in args:
            t = PY_TYPES[a.type]
            params.append(_inspect.Parameter(
                a.name, _inspect.Parameter.POSITIONAL_OR_KEYWORD,
                annotation=t if a.is_mandatory else _T.Optional[t],
                default=_inspect.Parameter.empty if a.is_mandatory else None,
            ))
        
        callback.__signature__ = _inspect.Signature(params)

        return _discord.app_commands.Command(name=operation.name, description=operation.description, callback=callback)

    def _set_operations(self, operations: _T.Sequence[_ai_chatbots.ChatbotOperation]) -> None:
        self.__operations = operations

    def __operations_state(self) -> tuple:
        return tuple(
            (operation.name, tuple((a.name, a.type, a.is_mandatory) for a in operation.arguments.values()))
            for operation in self.__operations
        )

    async def refresh_commands(self) -> None:
        state = self.__operations_state()
        
        if state == self.__last_tree_state:
            return

        self.__tree.clear_commands(guild=None)
        for operation in self.__operations:
            self.__tree.add_command(self.build_command(operation))
            
        await self.__tree.sync()
        self.__last_tree_state = state

    @_discord_ext_tasks.loop(minutes=1)
    async def __watch(self) -> None:
        await self.refresh_commands()

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
        self.__loop.create_task(self.__client.start(self.__token))

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
        if not self.__watch.is_running():
            self.__watch.start()

        assert self.__client.user
        
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

