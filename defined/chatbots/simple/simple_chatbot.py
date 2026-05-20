import ai.discussion as _ai_discussion
import ai.chatbots as _ai_chatbots
import ai.chatbot_data as _ai_chatbot_data

import interactions as _interactions

import json as _json
import local_utils.images as _local_utils_images
import traceback
import time as _time

class SimpleChatbot(_ai_chatbots.Chatbot):
    def __init__(self, name: str, specs: _ai_chatbot_data.ChatbotSpecs) -> None:
        super().__init__(name, specs)

        self.__prompt = self.specs.directory.get_resource("prompt.txt")

        if not self.__prompt.exists:
            self.__prompt.write_content("You are a helpful assistant")

    def answer_to_discussion(self, discussion: _ai_discussion.ChatbotDiscussion[_ai_discussion.ChatbotMessage[_ai_discussion.ChatbotSender]]) -> None:
        json_schema = discussion.get_json_schema()

        messages: list[_interactions.ChatCompletionMessage | _interactions.ChatCompletionTool.ChatCompletionToolResult] = [
            _interactions.ChatCompletionMessage('system', discussion.get_json_description_for_llm())
        ]

        for message in discussion.mixed_messages_with_tool_calls:
            if isinstance(message, _interactions.ChatCompletionTool.ChatCompletionToolResult):
                messages.append(message)
                continue
            
            images: list[_local_utils_images.Image] = []
            
            message_content = message.export_to_llm(self.specs, images)
            if not isinstance(message_content, str):
                message_content = _json.dumps(message_content)

            messages.append(_interactions.ChatCompletionMessage('assistant' if message.sender.is_self else 'user', message_content, images))
        
        result_message = self.complete(_interactions.ChatCompletionDescription(messages, json_schema, discussion_uuid=discussion.uuid, tools_advancement_follower=discussion), discussion)

        discussion.add_message_from_llm_response(self.specs, result_message)

    def run(self) -> None:
        while not self.should_stop:
            discussions = self.discussions

            for discussion in discussions:
                if discussion.has_unread_messages:
                    try:
                        self.answer_to_discussion(discussion)
                        discussion.mark_as_read()
                    except _interactions.InteractionInterruptionError:
                        pass
                    except Exception:
                        traceback.print_exc()
            
            _time.sleep(10)




