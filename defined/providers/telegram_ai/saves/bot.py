import saves as _saves
import typing as _T
import telegram as _telegram

from .discussion import TelegramDiscussionSaver

class TelegramBotSaver():
    def __init__(self, directory: _saves.ResourcesDirectory) -> None:
        self.__directory = directory

    @property
    def discussions_savers(self) -> _T.Sequence[TelegramDiscussionSaver]:
        discussions: list[TelegramDiscussionSaver] = []

        for directory_name in self.__directory.list_directories():
            if directory_name.startswith("tg-discussion-"):
                discussions.append(TelegramDiscussionSaver(self.__directory.get_directory(directory_name)))

        return discussions
    
    def get_discussion_saver(self, chat: _telegram.Chat) -> TelegramDiscussionSaver:
        return TelegramDiscussionSaver(self.__directory.get_directory('tg-discussion-' + str(chat.id)))
    

