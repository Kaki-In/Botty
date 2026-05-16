import ai.chatbot_data as _ai_chatbot_data
import ai.discussion as _ai_discussion

import interactions as _interactions

import typing as _T
import saves as _saves

class _discussion_cut_modifier_configuration(_T.TypedDict):
    last_interactions_count: int

class DiscussionCutModifier(_ai_discussion.ChatbotDiscussionModifier):
    def get_configuration_for(self, specs: _ai_chatbot_data.ChatbotSpecs) -> _discussion_cut_modifier_configuration:
        return _saves.ConfigurationFile[_discussion_cut_modifier_configuration](specs.configuration_directory.get_directory('discussion_cut').get_resource('config.json'), {
            'last_interactions_count': 25
        }).read_configuration()
    
    def modify_chat_completion(self, specs: _ai_chatbot_data.ChatbotSpecs, discussion: _ai_discussion.ChatbotDiscussion, description: _interactions.ChatCompletionDescription) -> _interactions.ChatCompletionDescription:
        last_interaction_count = self.get_configuration_for(specs)['last_interactions_count']

        return description.removing_messages(count_before=len(discussion.messages)-last_interaction_count)


