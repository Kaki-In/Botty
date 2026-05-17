from .telegram_message import TelegramChatbotMessage

from ..saves import TelegramDiscussionSaver

import interactions as _interactions
import ai.discussion as _ai_discussion, ai.chatbot_data as _ai_chatbot_data

import typing as _T
import telegram as _telegram
import telegram.constants as _telegram_constants
import asyncio as _asyncio
import json as _json
import traceback as _traceback

class TelegramChatbotDiscussion(_ai_discussion.ChatbotDiscussion[TelegramChatbotMessage]):
    def __init__(self, message_methods: _T.Sequence[_T.Type[TelegramChatbotMessage]], loop: _asyncio.AbstractEventLoop, creators: _interactions.CreatorsMap, creators_state: _interactions.CreatorsState, bot: _telegram.Bot, directory: TelegramDiscussionSaver) -> None:
        discussion_properties = directory.properties_saver.read_properties(bot)

        super().__init__(str(discussion_properties['chat'].id), creators_state)

        self.__chat = discussion_properties['chat']

        self.__message_methods = message_methods
        self.__loop = loop
        self.__creators = creators

        self.__messages = []

        for message_saver in directory.get_messages_savers():
            message_properties = message_saver.properties_file.read_message_properties(bot)

            for message_method in self.__message_methods:
                if message_method.class_get_messages_typename() == message_properties['message_type']:
                    self.__messages.append(message_method.load_back(message_properties['telegram_message'], message_saver.message_saves_directory))
        
        self.__directory = directory
        
    @property
    def has_unread_messages(self) -> bool:
        return not self.__directory.properties_saver.read_properties()['read']
    
    @property
    def chat(self) -> _telegram.Chat:
        return self.__chat

    @property
    def message_methods(self) -> _T.Sequence[_T.Type[TelegramChatbotMessage]]:
        return self.__message_methods
    
    @property
    def messages(self) -> _T.Sequence[TelegramChatbotMessage]:
        return self.__messages
    
    @property
    def tool_calls(self) -> _T.Sequence[_interactions.ChatCompletionTool.ChatCompletionToolResult]:
        return self.__directory.read_tool_calls()

    @property
    def directory(self) -> TelegramDiscussionSaver:
        return self.__directory
    
    @property
    def current_tool_message(self) -> _telegram.Message | None:
        return self.__directory.properties_saver.read_properties(self.__chat.get_bot())['current_tool_message']
    
    @current_tool_message.setter
    def current_tool_message(self, message: _telegram.Message | None) -> None:
        self.__directory.properties_saver.write_properties(self.__chat, not self.has_unread_messages, message)
    
    def add_message(self, message: TelegramChatbotMessage) -> None:
        self.__messages.append(message)
        self.save_message(message)

        self.creators_state.interrupt_all()

    def save_message(self, message: TelegramChatbotMessage) -> None:
        message_saver = self.__directory.get_message_saver(message.telegram_message)
        message_saver.properties_file.write_message_properties(message.telegram_message, message.class_get_messages_typename())

    def insert_message(self, position: int, message: TelegramChatbotMessage) -> None:
        self.__messages.insert(position, message)
        self.save_message(message)

        self.creators_state.interrupt_all()

    def delete_message(self, message: TelegramChatbotMessage) -> None:
        self.__messages.remove(message)
        
        message_saver = self.__directory.get_message_saver(message.telegram_message)
        message_saver.delete()

        self.creators_state.interrupt_all()

    def replace_message_with(self, uuid: str, new_message: TelegramChatbotMessage) -> None:
        for index, message in enumerate(self.messages):
            if message.uuid == uuid:
                self.delete_message(message)
                self.insert_message(index, new_message)
                return
        
        raise ReferenceError(f"message with uuid {uuid!r} not found")
    
    def get_message_method_from_telegram(self, message: _telegram.Message) -> _T.Type[TelegramChatbotMessage]:
        for message_method in self.message_methods:
            if message_method.accepts(message):
                return message_method
        
        raise TypeError("no method to build this messages")
    
    async def handle_message(self, specs: _ai_chatbot_data.ChatbotSpecs, update: _telegram.Update) -> bool:
        assert update.effective_chat
        assert update.effective_message

        is_edit = any((
            update.edited_message,
            update.edited_channel_post,
            update.edited_business_message,
        ))

        try:
            message_method = self.get_message_method_from_telegram(update.effective_message)
        except TypeError:
            try:
                await update.effective_message.delete()
            except:
                print("Could not handle message", update.effective_message)
            return False
        
        if update.effective_chat.type != _telegram_constants.ChatType.PRIVATE and not message_method.is_for_me(update.effective_message):
            return False
        
        message_saver = self.__directory.get_message_saver(update.effective_message)
        message_saver.properties_file.write_message_properties(update.effective_message, message_method.class_get_messages_typename())

        created_message = await message_method.create_from_telegram(update.effective_message, specs, self.__creators, self.creators_state, message_saver.message_saves_directory)

        if is_edit:
            self.replace_message_with(str(update.effective_message.id), created_message)
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
#                        'replying_to_old_message': {
#                            'type': ['integer', 'null'],
#                            'description': "(Optional) The identifier of a message to respond to, when clearly needed. Should stay unset or set to null most of the time.",
#                            'enum': [message.telegram_message.id for message in self.messages] + [None]
#
#                         }
                    },
                    'required': ['type', 'data'],
                    'additionalProperties': False
                }
                for message_method in self.message_methods
            ]
        }

    def get_json_schema_for_llm(self) -> _T.Any:
        return {
            'oneOf': [
                {
                    'type': 'object',
                    'properties': {
                        'type': {
                            'type': 'string',
                            'const': message_method.class_get_messages_typename()
                        },
                        'data': message_method.class_get_json_schema_for_llm(),
#                        'replying_to_old_message': {
#                            'type': ['integer', 'null'],
#                            'description': "(Optional) The identifier of a message to respond to, when clearly needed. Should stay unset or set to null most of the time.",
#                            'enum': [message.telegram_message.id for message in self.messages] + [None]
#                        }

                    },
                    'required': ['type', 'data']
                }
                for message_method in self.message_methods
            ]
        }

    def add_message_from_llm_response(self, specs: _ai_chatbot_data.ChatbotSpecs, response: str) -> None:
        self.current_tool_message = None
        
        data = _json.loads(response)
        
        assert isinstance(data, dict)

        for method in self.message_methods:
            if method.class_get_messages_typename() == data['type']:
                reply_to = data.get('replying_to_old_message')

                if len(self.messages) > 0 and reply_to == self.messages[-1].replies_to and self.messages[-1].is_from_self:
                    reply_to = None

                telegram_message, extras = _asyncio.run_coroutine_threadsafe(method.load_from_llm(self.__chat, specs, self.__creators, self.creators_state, data['data'], reply_to), self.__loop).result()

                message_saver = self.__directory.get_message_saver(telegram_message)
                message_saver.properties_file.write_message_properties(telegram_message, method.class_get_messages_typename())

                try:
                    message = _asyncio.run_coroutine_threadsafe(method.create_with_extras(telegram_message, specs, extras, message_saver.message_saves_directory), self.__loop).result()
                except Exception:
                    _traceback.print_exc()
                    message_saver.delete()
                    raise

                self.add_message(message)

    def get_context_prompt(self, specs: _ai_chatbot_data.ChatbotSpecs) -> str:
        # Need to load all files, so that they are both created
        private_context = specs.directory.get_directory("telegram").get_directory('conf').get_resource('private_prompt.txt')
        if not private_context.exists:
            private_context.write_content('You are speaking in a Telegram private discussion with {distant_username}. ')

        group_context = specs.directory.get_directory("telegram").get_directory('conf').get_resource('group_prompt.txt')
        if not group_context.exists:
            group_context.write_content('You are speaking in a Telegram public discussion named \"{discussion_name}\", containing {members_count} members.\nYou should stay quiet most of the time.')

        if self.__chat.type == _telegram_constants.ChatType.PRIVATE:
            return private_context.read_content().format(
                distant_username=self.__chat.username or "a single distant user"
            )
        else:
            return group_context.read_content().format(
                discussion_name = self.__chat.effective_name or self.__chat.id,
                members_count=_asyncio.run_coroutine_threadsafe(self.__chat.get_member_count(), self.__loop).result()
            )
            
    def mark_as_unread(self) -> None:
        self.__directory.properties_saver.write_properties(self.__chat, False, self.current_tool_message)
            
    def mark_as_read(self) -> None:
        self.__directory.properties_saver.write_properties(self.__chat, True, self.current_tool_message)
        
    def on_tool_started(self, tool: _interactions.ChatCompletionTool, args: _T.Mapping[str, _T.Any]) -> None:
        self.__loop.run_until_complete(self.prepare_tool_message(tool, args))

    def on_tool_update(self, tool: _interactions.ChatCompletionTool, args: _T.Mapping[str, _T.Any], event_data: str) -> None:
        self.__loop.run_until_complete(self.update_tool_message(tool, args, event_data))

    def on_tool_finished(self, tool: _interactions.ChatCompletionTool, result: _interactions.ChatCompletionTool.ChatCompletionToolResult) -> None:
        self.__loop.run_until_complete(self.remove_tool_message(tool, result))
    
    async def prepare_tool_message(self, tool: _interactions.ChatCompletionTool, args: _T.Mapping[str, _T.Any]) -> None:
        message = await self.__chat.send_message(f"Calling tool {tool.name}...")
        self.current_tool_message = message

    async def update_tool_message(self, tool: _interactions.ChatCompletionTool, args: _T.Mapping[str, _T.Any], event_data: str) -> None:
        if self.current_tool_message is None:
            await self.prepare_tool_message(tool, args)
        
        current_message = self.current_tool_message
        assert current_message is not None
        
        await current_message.edit_text(f"Calling tool {tool.name}...\n" + event_data)

    async def remove_tool_message(self, tool: _interactions.ChatCompletionTool, result: _interactions.ChatCompletionTool.ChatCompletionToolResult) -> None:
        self.__directory.save_tool_call(result)
        
        if self.current_tool_message is None:
            await self.prepare_tool_message(tool, result.args)
        
        current_message = self.current_tool_message
        assert current_message is not None
        
        await current_message.edit_text(f"{tool.name} action ended : \n" + result.result)
        

    




