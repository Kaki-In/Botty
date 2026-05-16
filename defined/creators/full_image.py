import local_utils.images as _local_utils_images
import typing as _T
import saves as _saves

import interactions as _interactions

class FullImageGeneratorFactory(_interactions.CreatorFactory[str, _local_utils_images.Image]):
    def __init__(self, image_setter_factory: _interactions.CreatorFactory[str, _interactions.ImageSettings], image_creator_factory: _interactions.CreatorFactory[_interactions.ImageSettings, _local_utils_images.Image]) -> None:
        super().__init__()

        self.__image_setter_factory = image_setter_factory
        self.__image_creator_factory = image_creator_factory

    def build_from(self, directory: _saves.ResourcesDirectory) -> 'FullImageGenerator':
        setter_directory = directory.get_directory("image_definer")
        creator_directory = directory.get_directory("image_creator")

        return FullImageGenerator(
            self.__image_setter_factory.build_from(setter_directory),
            self.__image_creator_factory.build_from(creator_directory)
        )

class FullImageGenerator(_interactions.Creator[str, _local_utils_images.Image]):
    def __init__(self, prompt_creator: _interactions.Creator[str, _interactions.ImageSettings], image_creator: _interactions.Creator[_interactions.ImageSettings, _local_utils_images.Image]) -> None:
        super().__init__()

        self.__prompt_creator = prompt_creator
        self.__image_creator = image_creator

    def _create_object_from(self, description: str) -> _local_utils_images.Image:
        image_settings = self.__prompt_creator._create_object_from(description)
        result = self.__image_creator._create_object_from(image_settings)
        return result

    def on_interruption(self) -> None:
        self.__prompt_creator.interrupt()
        self.__image_creator.interrupt()



