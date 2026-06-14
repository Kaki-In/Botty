import telegram as _telegram
import telegram.constants as _telegram_constants
import asyncio as _asyncio

class TelegramActionWaiting():
    def __init__(self, chat: _telegram.Chat, action: _telegram_constants.ChatAction) -> None:
        self.__should_stop = False
        self.__chat = chat
        self.__action = action
    
    async def main_action(self) -> None:
        i=8
        while not self.__should_stop:
            if i == 8:
                i = 0
                await self.__chat.send_chat_action(self.__action)

            await _asyncio.sleep(0.5)
            i += 1
        
    def __enter__(self):
        _asyncio.create_task(self.main_action())

    def __exit__(self, exc_type, exc, tb):
        self.__should_stop = True

