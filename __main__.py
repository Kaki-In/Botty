from defined.chatbots import *
from defined.creators import *
from defined.modifiers import *
from defined.processors import *
from defined.providers import *

from interactions import *

from ai.chatbots import *
from ai.chatbot_data import *

import saves
import threading
import local_utils.images 
import pathlib as pathlib

HOME_DIRECTORY = saves.ResourcesDirectory(str(pathlib.Path.home() / '.botty'))

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
        bot = RealisticChatbot(ChatbotSpecs(directory, HOME_DIRECTORY.get_directory(directory), ollama_creator_factory))
        bots_registry.add_chatbot(bot)
        
    # add discussion modifiers
    bots_registry.add_modifier_to_chatbots(TimeAwareChatbotModifier())
    bots_registry.add_modifier_to_chatbots(DiscussionCutModifier())
    bots_registry.add_modifier_to_chatbots(ToolsInserterDiscussionModifier(  )) # add your custom tools here
    
    bots_registry.add_processor_to_chatbots(SimplyPrintChatbotMessagesProcessor())
    
    ollama_embedder_factory = OllamaEmbedderFactory()
    query_factory = DiscussionExaminatorFactory(ollama_creator_factory, """You are a query parser for a vector-based memory. 
A discussion will be provided, and you must provide a query which allows to search in this memory. 

Queries must be natural-language words in the discussion language, which describes what to search. 

For instance : 

Discussion : (from bob) Hello ! Are you better since last evening ? 
Your possible answer : "feeling bad during evening"

You must only answer by the query without any comment. 
""")
    
    # Adds memory to bots
    for bot in bots_registry.chatbots:
        memory_factory = GlobalChatbotMemoryFactory(ChatbotVectorMemoryEvaluator(bot.specs.directory.get_directory('embedding-cache'), ollama_embedder_factory))
        preparator = ChatbotMemoryQueryBasedPreparator(query_factory, knowledge=(memory_factory, "Use this memory for any general knowledge"))
        modifier = ChatbotMemoriesDiscussionModifier([preparator], False)
        
        bot.add_discussion_modifier(modifier) # For the bot to remember back some elements. Tools allow the bot to explictly ask to save a remembering, but it is useless in this context. 
        bot.add_message_processor(ChatbotMemoryProcessor(modifier, bot.specs.configuration_directory.get_directory('memory_processor'), ollama_creator_factory)) # For the bot to automatically create its own rememberings

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


