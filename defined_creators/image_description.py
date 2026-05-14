from interactions import Creator, CreatorFactory
from .used_objects import ChatCompletionDescription, ChatCompletionMessage

import local_utils.images as _local_utils_images
import saves as _saves

class ImageDescriptorFactory(CreatorFactory[_local_utils_images.Image, str]):
    def __init__(self, chat_completor: CreatorFactory[ChatCompletionDescription, str]) -> None:
        self.__chat_completor = chat_completor

    def build_from(self, directory: _saves.ResourcesDirectory) -> 'ImageDescriptor':
        image_description_file = directory.get_resource("image_prompt.txt")

        if not image_description_file.exists:
            image_description_file.write_content("You are an image descriptor")

        return ImageDescriptor(self.__chat_completor.build_from(directory.get_directory("image_description")), image_description_file.read_content())

class ImageDescriptor(Creator[_local_utils_images.Image, str]):
    def __init__(self, chat_completor: Creator[ChatCompletionDescription, str], image_description: str) -> None:
        super().__init__()

        self.__chat_completor = chat_completor
        self.__image_description = image_description

    def _create_object_from(self, description: _local_utils_images.Image) -> str:
        messages = [
            ChatCompletionMessage('system', self.__image_description),
            ChatCompletionMessage('user', "Please describe the following image :\n[img-0]", [description])
        ]

        result = self.__chat_completor._create_object_from(ChatCompletionDescription(messages))
        return result
    
    def on_interruption(self) -> None:
        self.__chat_completor.interrupt()


