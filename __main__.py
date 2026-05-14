from defined_chatbots.realistic import *
from defined_modifiers.time_aware import TimeAwareChatbotModifier
from defined_creators import *
from interactions import *
from ai.chatbots import *
from ai.chatbot_data import *
from telegram_ai.handlers import TelegramBotHandler
from telegram_ai.telegram_messages import *
from telegram_ai.saves import *

import saves
import threading
import local_utils.images 
import pathlib as _pathlib

HOME_DIRECTORY = saves.ResourcesDirectory(str(_pathlib.Path.home() / '.botty'))

if __name__ == '__main__':
    ollama_creator_factory = OllamaChatCompletorFactory()

    creatorsMap = CreatorsMap()
    creatorsMap.add_creator_factory(FullImageGeneratorFactory(AIPromptGeneratorFactory(ollama_creator_factory), StableDiffusionImageGeneratorFactory()), str, local_utils.images.Image)
    creatorsMap.add_creator_factory(ImageDescriptorFactory(ollama_creator_factory), local_utils.images.Image, str)
    creatorsMap.add_creator_factory(SimplySleepCreatorFactory(), float, Sleepy)

    message_methods = [
        TelegramChatbotImageMessage,
        TelegramChatbotTextualMessage
    ]

    telegram_providers: list[TelegramBotHandler] = []

    bots_registry = ChatbotsRegistry()
    for directory in HOME_DIRECTORY.list_directories():
        bot = RealisticChatbot(directory, ChatbotSpecs(HOME_DIRECTORY.get_directory(directory), ollama_creator_factory))
        bots_registry.add_chatbot(bot)

        telegram_providers.append(TelegramBotHandler(bot, creatorsMap, CreatorsState(), message_methods))

    bots_registry.add_modifier_to_chatbots(TimeAwareChatbotModifier())
    bots_registry.start_all_chatbots()
    
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        print()
        print("Waiting for all processes to stop...")

        for provider in telegram_providers:
            provider.stop()

        bots_registry.stop_all_chatbots()




