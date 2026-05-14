from ai.chatbot_data import ChatbotSpecs
from ai.chatbots import ChatbotDiscussionModifier
from ai.discussion import ChatbotDiscussion

from defined_creators.used_objects.chat_completion import ChatCompletionDescription

import typing as _T
import saves as _saves

class _discussion_cut_modifier_configuration(_T.TypedDict):
    last_interactions_count: int

class DiscussionCutModifier(ChatbotDiscussionModifier):
    def get_configuration_for(self, specs: ChatbotSpecs) -> _discussion_cut_modifier_configuration:
        return _saves.ConfigurationFile[_discussion_cut_modifier_configuration](specs.configuration_directory.get_directory('discussion_cut').get_resource('config.json'), {
            'last_interactions_count': 25
        }).read_configuration()
    
    def modify_chat_completion(self, specs: ChatbotSpecs, discussion: ChatbotDiscussion, description: ChatCompletionDescription) -> ChatCompletionDescription:
        last_interaction_count = self.get_configuration_for(specs)['last_interactions_count']

        return description.removing_messages(count_before=len(discussion.messages)-last_interaction_count)


