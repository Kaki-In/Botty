import telegram as _telegram
import telegram.ext as _telegram_ext
import telegram.constants as _telegram_constants
import typing as _T
import datetime as _datetime
import asyncio as _asyncio
import traceback as _traceback
import threading as _threading

from defined_providers.telegram_ai.objects import TelegramChatbotDiscussion, TelegramChatbotMessage
from defined_providers.telegram_ai.saves import TelegramBotSaver, TelegramDiscussionSaver

from interactions import CreatorsMap, CreatorsState

from ai.chatbots import ChatbotDiscussionsProvider, Chatbot
from ai.discussion import ChatbotDiscussion
from ai.chatbot_data import ChatbotSpecs

class TelegramBotHandler(ChatbotDiscussionsProvider):
    def __init__(self, chatbot: Chatbot, creators_map: CreatorsMap, creators_state: CreatorsState, message_methods: _T.Sequence[_T.Type[TelegramChatbotMessage]], directly_start: bool=True) -> None:
        tg_directory = chatbot.specs.directory.get_directory('telegram')
        tg_token_file = tg_directory.get_resource('token')

        if not (tg_token_file.exists and (token:=tg_token_file.read_content().replace(" ", '').replace("\n", '')) != ''):
            tg_token_file.write_content('')
            raise ValueError("Please provide a token in file "+repr(tg_token_file.path))

        self.__directory = TelegramBotSaver(tg_directory.get_directory('discussions'))
        self.__creators_map = creators_map
        self.__creators_state = creators_state
        self.__message_methods = list(message_methods)

        self.__chatbot = chatbot
        self.__chatbot.add_discussion_provider(self)

        app = _telegram_ext.ApplicationBuilder().token(token).build()

        app.add_handler(_telegram_ext.CommandHandler("start", self._start))
        app.add_handler(_telegram_ext.CommandHandler("stop", self._stop))
        app.add_handler(_telegram_ext.MessageHandler(_telegram_ext.filters.COMMAND, self._handle_command))
        app.add_handler(_telegram_ext.MessageHandler(_telegram_ext.filters.ALL, self._handle_message))

        self.__app = app
        self.__loop = _asyncio.new_event_loop()

        self.__thread = _threading.Thread(target=self.run)

        if directly_start:
            self.start()

    @property
    def interactors_map(self) -> CreatorsMap:
        return self.__creators_map
    
    @property
    def message_methods(self) -> _T.Sequence[_T.Type[TelegramChatbotMessage]]:
        return self.__message_methods
    
    def start(self) -> None:
        self.__thread.start()
    
    def run(self) -> None:
        _asyncio.set_event_loop(self.__loop)
        self.__app.run_polling(stop_signals=None)
    
    def stop(self):
        self.__loop.stop()
        self.__creators_state.interrupt_all()

    def _get_discussion_saver(self, chat: _telegram.Chat) -> TelegramDiscussionSaver:
        return self.__directory.get_discussion_saver(chat)
    
    def get_discussion_or_create(self, chat: _telegram.Chat) -> TelegramChatbotDiscussion:
        saver = self._get_discussion_saver(chat)

        if not saver.properties_saver.exists:
            saver.properties_saver.write_properties(chat, _datetime.datetime.fromtimestamp(0, _datetime.UTC))

        return TelegramChatbotDiscussion(self.__message_methods, self.__loop, self.__creators_map, self.__creators_state, chat.get_bot(), saver)

    def delete_discussion(self, discussion: TelegramChatbotDiscussion) -> None:
        saver = self._get_discussion_saver(discussion.chat)
        saver.delete()

        discussion.creators_state.interrupt_all()

    async def _with_discussion(self, chat: _telegram.Chat, func: _T.Callable[[TelegramChatbotDiscussion], _T.Coroutine[None, None, _T.Any]]) -> None:
        discussion = self.get_discussion_or_create(chat)
        await func(discussion)

    async def _start(self, update: _telegram.Update, context: _telegram_ext.ContextTypes.DEFAULT_TYPE):
        assert update.effective_chat and update.effective_message
        self.get_discussion_or_create(update.effective_chat)

    async def _stop(self, update: _telegram.Update, context: _telegram_ext.ContextTypes.DEFAULT_TYPE):
        assert update.effective_chat

        discussion = self.get_discussion_or_create(update.effective_chat)
        self.delete_discussion(discussion)

    async def _handle_command(self, update: _telegram.Update, context: _telegram_ext.ContextTypes.DEFAULT_TYPE):
        assert update.effective_message

        try:
            await update.effective_message.delete()
        except Exception:
            print("Could not handle message", update.effective_message)

    async def _handle_message(self, update: _telegram.Update, context: _telegram_ext.ContextTypes.DEFAULT_TYPE):
        assert update.effective_chat
        assert update.effective_message

        is_new = any((
            update.message,
            update.channel_post,
            update.business_message,
        ))

        is_edit = any((
            update.edited_message,
            update.edited_channel_post,
            update.edited_business_message,
        ))

        if not (is_new or is_edit):
            return
        
        try:
            discussion = self.get_discussion_or_create(update.effective_chat)
            await discussion.handle_message(self.__chatbot.specs, update)
        except Exception:
            _traceback.print_exc()

    @property
    def app(self) -> _telegram_ext.Application:
        return self.__app

    def load_all_discussions(self, specs: ChatbotSpecs) -> _T.Sequence[ChatbotDiscussion]:
        # Don't need to use specs because this discussion provider is directly linked to the chatbot

        discussions: list[TelegramChatbotDiscussion] = []

        if self.__app.bot._bot_user is None:
            return []

        for discussion_saver in self.__directory.discussions_savers:
            discussion = TelegramChatbotDiscussion(self.__message_methods, self.__loop, self.__creators_map, self.__creators_state, self.__app.bot, discussion_saver)

            if len(discussion.messages) > 0 or discussion.chat.type == _telegram_constants.ChatType.PRIVATE:
                discussions.append(discussion)

        return discussions


