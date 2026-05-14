import abc as _abc
import typing as _T
import threading as _threading

from .discussion_provider import ChatbotDiscussionsProvider
from .discussion_modifier import ChatbotDiscussionModifier

from defined_creators.used_objects import ChatCompletionDescription

from ai.discussion import ChatbotDiscussion
from ai.chatbot_data import ChatbotSpecs

class Chatbot(_abc.ABC):
    _subclasses = {}
    _defined_elements = {}

    def __init__(self, name: str, specs: ChatbotSpecs, modifiers: _T.Optional[_T.Sequence[ChatbotDiscussionModifier]] = None) -> None:
        super().__init__()

        self.__name = name
        self.__specs = specs
        self.__thread = _threading.Thread(target=self.run)
        self.__discussions_providers: list[ChatbotDiscussionsProvider] = []
        self.__modifiers = list(modifiers or [])

        self.__should_stop = False

    @property
    def name(self) -> str:
        return self.__name
    
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
    def discussions(self) -> _T.Sequence[ChatbotDiscussion]:
        discussions: list[ChatbotDiscussion] = []

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
    
    def get_discussion_by_id[discussionType: ChatbotDiscussion](self, uuid: str, discussionType: _T.Type[discussionType]) -> discussionType:
        for discussion in self.discussions:
            if discussion.uuid == uuid:
                if isinstance(discussion, discussionType):
                    return discussion
            
        raise ReferenceError("discussion not found")
    
    def complete(self, messages: ChatCompletionDescription, discussion: ChatbotDiscussion) -> str:
        for modifier in self.__modifiers:
            messages = modifier.modify_chat_completion(self.__specs, discussion, messages)

        return discussion.creators_state.create_from_factory(self.__specs.messages_creator, messages, self.__specs.configuration_directory.get_directory("main_chat_completion"))

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
    

