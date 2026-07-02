import ai.chatbots as _ai_chatbots
import ai.chatbot_data as _ai_chatbot_data
import ai.discussion as _ai_discussion

class SimplyPrintChatbotMessagesProcessor(_ai_chatbots.ChatbotMessageProcessor):
    def process_message(self, message: _ai_discussion.ChatbotMessage, from_discussion: _ai_discussion.ChatbotDiscussion, specs: _ai_chatbot_data.ChatbotSpecs) -> None:
        images = []
        
        message_export = message.export_to_llm(specs, images)
        
        print("----")
        print('From discussion', from_discussion.uuid)
        print(message_export)
        print(f"({len(images)} images)")
        print("----")



