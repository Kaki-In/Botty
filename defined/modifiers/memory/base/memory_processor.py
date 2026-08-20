import ai.chatbot_data as _ai_chatbot_data
import ai.chatbots as _ai_chatbots
import ai.discussion as _ai_discussion

from .memory_discussion_modifier import ChatbotMemoriesDiscussionModifier
from .memory import ChatbotMemory

import typing as _T
import interactions as _interactions
import json as _json
import datetime as _datetime
import saves as _saves

class _remembering_response_object(_T.TypedDict):
    fact: str
    confidence: float
    relevance: float
    context: dict[str, _T.Any]

class _remembering_global_configuration_object(_T.TypedDict):
    load_messages_back: int

class _remembering_thresholds_configuration_object(_T.TypedDict):
    min_confidence: float
    min_relevance: float

class _memory_info_object(_T.TypedDict):
    memory: ChatbotMemory
    rememberings: _T.Sequence[_T.Any]  # remplacer par le vrai type des rememberings si connu
    configuration: _remembering_thresholds_configuration_object
    description: str

class ChatbotMemoryProcessor(_ai_chatbots.ChatbotMessageProcessor):
    def __init__(self, modifier: ChatbotMemoriesDiscussionModifier, directory: _saves.ResourcesDirectory, creator_factory: _interactions.CreatorFactory[_interactions.ChatCompletionDescription, _interactions.ChatCompletionResult]) -> None:
        super().__init__()
        
        self.__modifier = modifier
        self.__directory = directory
        self.__creator_factory = creator_factory
        self.__state = _interactions.CreatorsState()
        
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
    
    def process_message(self, message: _ai_discussion.ChatbotMessage[_ai_discussion.ChatbotSender], from_discussion: _ai_discussion.ChatbotDiscussion[_ai_discussion.ChatbotMessage[_ai_discussion.ChatbotSender]], specs: _ai_chatbot_data.ChatbotSpecs) -> None:
        pass
    
    def process_messages(self, messages: _T.Sequence[_ai_discussion.ChatbotMessage[_ai_discussion.ChatbotSender]], from_discussion: _ai_discussion.ChatbotDiscussion[_ai_discussion.ChatbotMessage[_ai_discussion.ChatbotSender]], specs: _ai_chatbot_data.ChatbotSpecs) -> None:
        for preparator in self.__modifier.memory_preparators:
            all_rememberings = preparator.get_rememberings_for(self.__state, from_discussion, specs)

            if not all_rememberings:
                continue

            state = _interactions.CreatorsState()

            global_configuration_file = _saves.ConfigurationFile[_remembering_global_configuration_object](
                self.__directory.get_resource('config.json'),
                {
                    'load_messages_back': 10
                }
            )
            global_configuration = global_configuration_file.read_configuration()

            memory_infos: dict[str, _memory_info_object] = {}

            for memory_name, (memory, rememberings) in all_rememberings.items():
                memory_settings_directory = self.__directory.get_directory('memory:' + memory_name)

                configuration_file = _saves.ConfigurationFile[_remembering_thresholds_configuration_object](
                    memory_settings_directory.get_resource('config.json'),
                    {
                        'min_confidence': 0.5,
                        'min_relevance': 0.5
                    }
                )
                configuration = configuration_file.read_configuration()

                memory_infos[memory_name] = {
                    'memory': memory,
                    'rememberings': rememberings,
                    'configuration': configuration,
                    'description': memory.description,
                }

            memories_block = "\n\n".join(
                f'- "{name}": {info["description"]}'
                for name, info in memory_infos.items()
            )

            prompt_file = self.__directory.get_resource('memory-creation-prompt.txt')

            if not prompt_file.exists:
                prompt_file.write_content("""You are a memory system for {bot_name}.

You will be given a chunk of recent conversation. Your job is to find every piece of information worth permanently remembering, and assign each one to the single best-fitting memory below.

## Available memories
For each fact you find, you must assign it to exactly ONE of these memories — the one it fits best. If a fact could vaguely fit several, pick the single best match, not all of them. If a fact doesn't clearly belong to any of them, don't record it at all.

{memories_block}

## What counts as worth remembering
Only record information that is:
- Durable: still true or relevant days/weeks later (not "what was just said", not a one-off question)
- Specific: a concrete fact, preference, decision, or event — not a vague impression
- A clear match for one specific memory above — not just loosely related to several

Do NOT record:
- Small talk, greetings, jokes, or filler with no lasting content
- Questions the user asked without revealing anything about themselves
- Information already covered by an existing memory (see below)
- Anything you're not confident actually happened or was actually said

A single message can contain multiple separate facts, possibly belonging to different memories. Treat each one as its own item in the output array — do not merge them into one fact, and do not stop at the first fact you find.

Example: "I moved to Lyon last month, and I also just adopted a cat."
→ two separate facts, possibly in different memories: one about the move, one about the cat.

The conversation may cover completely mundane or unrelated topics. That is expected and fine — if nothing is worth remembering, return an empty array. An empty array is a correct and common answer. Do not force a memory just to produce output.
""".format(bot_name=specs.name, memories_block=memories_block))

            system_prompt = prompt_file.read_content() + """

## Output format
Return a JSON object with one key per memory listed above. Each key maps to
an array of facts belonging to that memory (an empty array if none).

Each fact in an array has:
- `fact`: a single fact, written in your own words as a new, standalone statement
- `context`: an object with:
    - `topic`: short label for what this is about (string)
    - `source`: where or who brought you to this fact
- `confidence`: how sure you are this is accurate and worth keeping, from 0.00 to 1.00.
    - 0.90–1.00: an information that has been stated by something trustable
    - 0.50–0.80: something that seems to be true, but one cannot prove it using this discussion
    - below 0.50: seems like a rumor, something not checkable, or anything totally invented.
- `relevance`: how useful this fact would be to recall in a future conversation, from 0.00 to 1.00.
    - 0.90–1.00: a core fact you'd want to know before any future interaction (strong preference, key relationship, recurring need)
    - 0.50–0.80: a minor but genuine fact worth keeping
    - below 0.50: marginal — you're recording it mostly because it was mentioned, not because it matters.

`fact` must be a rewritten statement, never a sentence copied from the conversation.
Even if the original message already sounds clear and grammatically complete, you
must still rewrite it as an independent statement — do not just repeat the words
used in the conversation. It must also stand alone: someone reading only this
fact, with no access to the conversation, must understand it fully. Resolve any
reference (pronouns, "the X", names without context) using earlier messages
before writing it.

Bad (copied from the message, and unresolved): "She works there."
Bad (still just copied, even though grammatically complete): "I work at the downtown clinic."
Good (rewritten as an independent, resolved statement): "Maria works at the downtown clinic."

If you can't resolve a reference with confidence, don't record that fact.
"""

            discussion_messages = ""
            images = []

            for message in from_discussion.messages[-global_configuration['load_messages_back']:]:
                discussion_messages += " - From ({username}) : \n{message}\n\n".format(
                    username=message.sender.export_to_llm(),
                    message=message.export_to_llm(specs, images)
                )

            rememberings_json_schema = {
                'type': 'object',
                'properties': {
                    memory_name: {
                        'type': 'array',
                        'maxItems': 5,
                        'items': {
                            'type': 'object',
                            'required': ['fact', 'context', 'confidence', 'relevance'],
                            'properties': {
                                'fact': {
                                    'type': 'string',
                                    'description': 'A fact rewritten in your own words as a standalone statement — never a sentence copied from the conversation'
                                },
                                'context': {
                                    'type': 'object',
                                    'properties': {
                                        'topic': {'type': 'string'},
                                        'source': {'type': 'string'}
                                    },
                                    'required': ['topic', 'source']
                                },
                                'confidence': {'type': 'number', 'minimum': 0, 'maximum': 1},
                                'relevance': {'type': 'number', 'minimum': 0, 'maximum': 1},
                            }
                        }
                    }
                    for memory_name in memory_infos.keys()
                },
                'required': list(memory_infos.keys())
            }

            description = _interactions.ChatCompletionDescription(
                [
                    _interactions.ChatCompletionMessage('system', system_prompt),
                    _interactions.ChatCompletionMessage('user', "Please find rememberings in this discussion : \n\n" + discussion_messages, images)
                ],
                json_schema=rememberings_json_schema
            )

            existing_blocks = [
                f'Existing rememberings in memory "{memory_name}":\n' + '\n\n --- \n\n'.join(str(r) for r in info['rememberings'])
                for memory_name, info in memory_infos.items()
                if info['rememberings']
            ]

            if existing_blocks:
                description = description.adding_message_just_after_system_prompt(
                    _interactions.ChatCompletionMessage(
                        'system',
                        "Here are the rememberings that already exist, grouped by memory. You must NOT create these rememberings again:\n\n"
                        + '\n\n=====\n\n'.join(existing_blocks)
                    )
                )

            results: dict[str, list[dict]] = _json.loads(
                state.create_from_factory(self.__creator_factory, description, self.__directory.get_directory('remembering_resolver')).result
            )

            for memory_name, facts in results.items():
                import termcolor
                
                info = memory_infos[memory_name]
                configuration = info['configuration']

                for remembering_description in facts:
                    if (remembering_description['confidence'] < configuration['min_confidence']
                            or remembering_description['relevance'] < configuration['min_relevance']):
                        termcolor.cprint(memory_name + " " + str(remembering_description), color=(255, 0, 0))
                        continue

                    termcolor.cprint(memory_name + " " + str(remembering_description), color=(0, 255, 0))
                    info['memory'].save_remembering(
                        info['memory'].Remembering(
                            remembering_description['fact'],
                            remembering_description['context'],
                            _datetime.datetime.now()
                        )
                    )