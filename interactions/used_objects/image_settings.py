import local_utils.images as _local_utils_images
import typing as _T

class ImageSettings():
    def __init__(self, width: int, height: int, requires_controlnet: bool, prompt: str, controlnet_image: _T.Optional[_local_utils_images.Image] = None) -> None:
        self.__width = width
        self.__height = height
        self.__requires_controlnet = requires_controlnet
        self.__prompt = prompt
        self.__image = controlnet_image
    
    @property
    def width(self) -> int:
        return self.__width
    
    @property
    def height(self) -> int:
        return self.__height
    
    @property
    def requires_controlnet(self) -> bool:
        return self.__requires_controlnet
    
    @property
    def prompt(self) -> str:
        return self.__prompt
    
    @property
    def control_net_image(self) -> _local_utils_images.Image | None:
        return self.__image
    

class ImageDescription():
    def __init__(self, description: str, image: _T.Optional[_local_utils_images.Image] = None) -> None:
        self.__description = description
        self.__image = image
    
    @property
    def description(self) -> str:
        return self.__description
    
    @property
    def image(self) -> _local_utils_images.Image | None:
        return self.__image

