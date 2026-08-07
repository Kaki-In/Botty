import abc as _abc
import typing as _T
import threading as _threading

import interactions as _interactions

from ..discussion import ChatbotDiscussion, ChatbotSender, ChatbotMessage
from ..chatbot_data import ChatbotSpecs

from .discussion_provider import ChatbotDiscussionsProvider
from .discussion_modifier import ChatbotDiscussionModifier
from .message_processor import ChatbotMessageProcessor

class Chatbot(_abc.ABC):
    _subclasses = {}
    _defined_elements = {}

    def __init__(self, specs: ChatbotSpecs, modifiers: _T.Optional[_T.Sequence[ChatbotDiscussionModifier]] = None, processors: _T.Optional[_T.Sequence[ChatbotMessageProcessor]] = None) -> None:
        super().__init__()

        self.__specs = specs
        self.__thread = _threading.Thread(target=self.run)
        self.__discussions_providers: list[ChatbotDiscussionsProvider] = []
        self.__modifiers = list(modifiers or [])
        self.__messages_processors = list(processors or [])

        self.__should_stop = False

    @property
    def name(self) -> str:
        return self.__specs.name
    
    @property
    def discussions_providers(self) -> _T.Sequence[ChatbotDiscussionsProvider]:
        return self.__discussions_providers
    
    @property
    def specs(self) -> ChatbotSpecs:
        return self.__specs
    
    @property
    def should_stop(self) -> bool:
        return self.__should_stop
    
    @property
    def processors(self) -> _T.Sequence[ChatbotMessageProcessor]:
        return self.__messages_processors

    @property
    def discussions(self) -> _T.Sequence[ChatbotDiscussion[ChatbotMessage[ChatbotSender]]]:
        discussions: list[ChatbotDiscussion[ChatbotMessage[ChatbotSender]]] = []

        for discussion_provider in self.__discussions_providers:
            discussions += discussion_provider.load_all_discussions(self.__specs)
        
        return discussions
    
    @property
    def modifiers(self) -> _T.Sequence[ChatbotDiscussionModifier]:
        return self.__modifiers
    
    def add_discussion_modifier(self, modifier: ChatbotDiscussionModifier) -> None:
        self.__modifiers.append(modifier)

    def remove_discussion_modifier(self, modifier: ChatbotDiscussionModifier) -> None:
        self.__modifiers.remove(modifier)
    
    def add_discussion_provider(self, provider: ChatbotDiscussionsProvider) -> None:
        self.__discussions_providers.append(provider)
        
    def add_message_processor(self, processor: ChatbotMessageProcessor) -> None:
        self.__messages_processors.append(processor)
    
    def get_discussion_by_id[discussionType: ChatbotDiscussion](self, uuid: str, discussionType: _T.Type[discussionType]) -> discussionType:
        for discussion in self.discussions:
            if discussion.uuid == uuid:
                if isinstance(discussion, discussionType):
                    return discussion
            
        raise ReferenceError("discussion not found")
    
    def complete(self, description: _interactions.ChatCompletionDescription, discussion: ChatbotDiscussion) -> str:
        for modifier in reversed(self.__modifiers):
            description = description.adding_editor_before(lambda description, m=modifier: m.modify_chat_completion(self.__specs, discussion, description))

        result = discussion.creators_state.create_from_factory(self.__specs.messages_creator, description, self.__specs.configuration_directory.get_directory("main_chat_completion"))
        
        return result.result
    
    def _process_new_messages(self) -> None:
        for provider in self.__discussions_providers:
            new_discussion_messages: list[tuple[ChatbotDiscussion, list[ChatbotMessage]]] = []
            
            while provider.has_next_added_messages(self.__specs):
                message, discussion = provider.next_added_message(self.__specs)
                
                for processor in self.__messages_processors:
                    processor.process_message(message, discussion, self.__specs)

                if any(i[0] == discussion for i in new_discussion_messages):
                    [i[1] for i in new_discussion_messages if i[0] == discussion][0].append(message)
                else:
                    new_discussion_messages.append((discussion, [message]))
            
            for discussion, new_messages in new_discussion_messages:
                for processor in self.__messages_processors:
                    processor.process_messages(new_messages, discussion, self.__specs)
    
    @_abc.abstractmethod
    def run(self) -> None:
        ...

    def start(self) -> None:
        self.__thread.start()

    def stop(self) -> None:
        self.__should_stop = True

        try:
            self.__thread.join()
        except:
            pass
    

