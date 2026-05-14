class ImageSettings():
    def __init__(self, width: int, height: int, is_self_face: bool, prompt: str) -> None:
        self.__width = width
        self.__height = height
        self.__is_self_face = is_self_face
        self.__prompt = prompt
    
    @property
    def width(self) -> int:
        return self.__width
    
    @property
    def height(self) -> int:
        return self.__height
    
    @property
    def is_self_face(self) -> bool:
        return self.__is_self_face
    
    @property
    def prompt(self) -> str:
        return self.__prompt
    

