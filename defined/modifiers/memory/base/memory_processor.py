import ai.chatbot_data as _ai_chatbot_data
import ai.chatbots as _ai_chatbots
import ai.discussion as _ai_discussion

from .memory_discussion_modifier import ChatbotMemoriesDiscussionModifier

import typing as _T
import interactions as _interactions
import json as _json
import datetime as _datetime
import saves as _saves

class _remembering_response_object(_T.TypedDict):
    sentence: str
    context: dict[str, _T.Any]

class _remembering_configuration_object(_T.TypedDict):
    load_messages_back: int
    min_confidence: float
    min_relevance: float

class ChatbotMemoryProcessor(_ai_chatbots.ChatbotMessageProcessor):
    def __init__(self, modifier: ChatbotMemoriesDiscussionModifier, directory: _saves.ResourcesDirectory, creator_factory: _interactions.CreatorFactory[_interactions.ChatCompletionDescription, _interactions.ChatCompletionResult]) -> None:
        super().__init__()
        
        self.__modifier = modifier
        self.__directory = directory
        self.__creator_factory = creator_factory
        self.__state = _interactions.CreatorsState()
        self.__configuration = _saves.ConfigurationFile[_remembering_configuration_object](self.__directory.get_resource('config.json'), {
            'load_messages_back': 10,
            'min_confidence': 0.5,
            'min_relevance': 0.5
        })
        
    @property
    def modifier(self) -> ChatbotMemoriesDiscussionModifier:
        return self.__modifier
    
    @property
    def directory(self) -> _saves.ResourcesDirectory:
        return self.__directory
        
    @property
    def creator_factory(self) -> _interactions.CreatorFactory[_interactions.ChatCompletionDescription, _interactions.ChatCompletionResult]:
        return self.__creator_factory
    
    @property
    def creators_state(self) -> _interactions.CreatorsState:
        return self.__state
    
    def process_message(self, message: _ai_discussion.ChatbotMessage, from_discussion: _ai_discussion.ChatbotDiscussion, specs: _ai_chatbot_data.ChatbotSpecs) -> None:
        pass
    
    def process_messages(self, messages: _T.Sequence[_ai_discussion.ChatbotMessage], from_discussion: _ai_discussion.ChatbotDiscussion, specs: _ai_chatbot_data.ChatbotSpecs) -> None:
        for preparator in self.__modifier.memory_preparators:
            all_rememberings = preparator.get_rememberings_for(self.__state, from_discussion, specs)
            
            for memory_name, (memory, rememberings) in all_rememberings.items():
                state = _interactions.CreatorsState()
                
                rememberings_json_schema = {
                    'type': 'array',
                    'maxItems': 5,
                    'items': {
                        'type': 'object',
                        'required': ['sentence', 'context'],
                        'properties': {
                            'sentence': {
                                'type': 'string',
                                'description': 'A single self-contained, factual sentence worth remembering long-term'
                            },
                            'context': {
                                'type': 'object',
                                'properties': {
                                    'topic': {'type': 'string'},
                                    'confidence': {'type': 'number', 'minimum': 0, 'maximum': 1},
                                    'relevance': {'type': 'number', 'minimum': 0, 'maximum': 1},
                                    'source': {'type': 'string'}
                                },
                                'required': ['topic', 'confidence', 'relevance', 'source']
                            }
                        }
                    }
                }
                
                prompt_file = self.__directory.get_resource(memory_name + '.txt')
                
                if not prompt_file.exists:
                    prompt_file.write_content("""You are a memory extraction system for {bot_name}.

You will be given a chunk of recent conversation. Your job is to decide whether any of it contains information worth permanently remembering for the "{name}" memory, and if so, extract it.

## What this memory is for
{description}

## What counts as worth remembering
Only extract information that is:
- Durable: still true or relevant days/weeks later (not "what was just said", not a one-off question)
- Specific: a concrete fact, preference, decision, or event — not a vague impression
- Actually relevant to the purpose of THIS memory ("{name}"), described above

Do NOT extract:
- Small talk, greetings, jokes, or filler with no lasting content
- Questions the user asked without revealing anything about themselves
- Information already covered by an existing remembering (see below)
- Anything you're not confident actually happened or was actually said

The conversation may cover completely mundane or unrelated topics. That is expected and fine — if nothing in it is worth remembering, return an empty array. An empty array is a correct and common answer. Do not force an extraction just to produce output.
""".format(bot_name = specs.name, name = memory_name, description = memory.description))
                    
                configuration = self.__configuration.read_configuration()
                
                discussion_messages = "Here are the discussion messages : \n\n"
                
                images=[]
                
                for message in from_discussion.messages[-configuration['load_messages_back']:]:
                    discussion_messages += " - From ({username}) : \n{message}\n\n".format(username=message.sender.export_to_llm(), message=message.export_to_llm(specs, images))
                    
                description = _interactions.ChatCompletionDescription(
                    [
                        _interactions.ChatCompletionMessage('system', prompt_file.read_content() + """
## Output format
Return a JSON array. Each item has:
- `sentence`: a single self-contained factual sentence (someone should understand it without seeing the original conversation)
- `context`: an object with:
    - `topic`: short label for what this is about (string)
    - `confidence`: how sure you are this is accurate and worth keeping, from 0 to 1
    - `relevance`: how useful this fact would be to recall in a future conversation, from 0 to 1.
        - 0.9–1.0: a core fact you'd want to know before any future interaction (strong preference, key relationship, recurring need)
        - 0.5–0.8: a minor but genuine fact worth keeping
        - below 0.5: marginal — you're extracting it mostly because it was mentioned, not because it matters.
        
    - `source` : where or who brought you to this sentence

If there is nothing new and worth keeping, return an empty array: []
"""),
                        _interactions.ChatCompletionMessage('user', "Please extract some rememberings on this discussion : \n\n" + discussion_messages, images)
                    ],
                    json_schema=rememberings_json_schema
                )
                
                if rememberings:
                    description = description.adding_message_after(
                        _interactions.ChatCompletionMessage(
                            'system',
                            f"There are some rememberings you already have from memory \"{memory_name}\" : \n\n" + '\n\n --- \n\n'.join(str(remembering) for remembering in rememberings) + "\n\nYou must only create new rememberings, if there are some."
                        )
                    )
                    
                results: list[_remembering_response_object] = _json.loads(state.create_from_factory(self.__creator_factory, description, self.__directory.get_directory('remembering_resolver')).result)
                
                for remembering_description in results:
                    if remembering_description['context'].get('confidence', 1) < configuration['min_confidence']:
                        continue
                    
                    memory.save_remembering(memory.Remembering(remembering_description['sentence'], remembering_description['context'], _datetime.datetime.now()))


