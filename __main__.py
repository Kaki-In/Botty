from defined.chatbots import *
from defined.modifiers import *
from defined.providers import *
from defined.creators import *

from interactions import *

from ai.chatbots import *
from ai.chatbot_data import *

import saves
import threading
import local_utils.images 
import pathlib as _pathlib

HOME_DIRECTORY = saves.ResourcesDirectory(str(_pathlib.Path.home() / '.botty'))

if __name__ == '__main__':
    # The main completor. Can be switched with Open AI or any other
    ollama_creator_factory = OllamaChatCompletorFactory()

    # The Telegram Messages used
    telegram_message_methods = [
        TelegramChatbotImageMessage,
        TelegramChatbotTextualMessage
    ]

    # The Discord Messages used
    discord_message_methods = [
        DiscordChatbotImageMessage,
        DiscordChatbotTextualMessage
    ]

    # Starting all bots
    bots_registry = ChatbotsRegistry()
    for directory in HOME_DIRECTORY.list_directories():
        bot = RealisticChatbot(directory, ChatbotSpecs(HOME_DIRECTORY.get_directory(directory), ollama_creator_factory))
        bots_registry.add_chatbot(bot)
        
    # add discussion modifiers
    bots_registry.add_modifier_to_chatbots(TimeAwareChatbotModifier())
    bots_registry.add_modifier_to_chatbots(DiscussionCutModifier())
    bots_registry.add_modifier_to_chatbots(ToolsInserterDiscussionModifier(  )) # add your custom tools here
    
    ollama_embedder_factory = OllamaEmbedderFactory()
    query_factory = MemoryQueryCreatorFactory(ollama_creator_factory)
    bots_registry.add_modifier_to_chatbots(ChatbotMemoryDiscussionModifier(GlobalChatbotMemoryFactory(ollama_embedder_factory), CreatorsState(), query_factory, 'knowledge', "Use this memory for any general knowledge"))

    # Providers need to be stopped separately
    telegramProvider = MainTelegramBotsHandler(*telegram_message_methods)
    discordProvider = MainDiscordBotsHandler(*discord_message_methods)
    
    bots_registry.add_provider_to_chatbots(telegramProvider)
    bots_registry.add_provider_to_chatbots(discordProvider)

    # All conversions that can be operated during the discussion for telegram bots. 
    telegramProvider.add_creator_factory(FullImageGeneratorFactory(AIPromptGeneratorFactory(ollama_creator_factory), StableDiffusionImageGeneratorFactory()), str, local_utils.images.Image)
    telegramProvider.add_creator_factory(ImageDescriptorFactory(ollama_creator_factory), local_utils.images.Image, ChatCompletionResult)
    telegramProvider.add_creator_factory(SimplySleepCreatorFactory(), float, Sleepy)
    
    discordProvider.add_creator_factory(FullImageGeneratorFactory(AIPromptGeneratorFactory(ollama_creator_factory), StableDiffusionImageGeneratorFactory()), str, local_utils.images.Image)
    discordProvider.add_creator_factory(ImageDescriptorFactory(ollama_creator_factory), local_utils.images.Image, ChatCompletionResult)
    discordProvider.add_creator_factory(SimplySleepCreatorFactory(), float, Sleepy)
    
    # Start bots
    bots_registry.start_all_chatbots()
    
    try:
        print("Waiting...")
        threading.Event().wait()
    except KeyboardInterrupt:
        print()
        print("Waiting for all processes to stop...")

        # First stop all discussions (and their creators states)
        telegramProvider.stop_all_bots()

        discordProvider.stop_all_bots()
        
        # Then, you can stop the chatbots which simply don't do anything. 
        bots_registry.stop_all_chatbots()


