import typing as _T
import pyvips as _pyvips
import base64 as _base64

class Image():
    def __init__(self, image: _T.Optional[_pyvips.Image] = None):
        self._image = image or _pyvips.Image.black(10, 10)                  #type:ignore

    def __str__(self) -> str:
        return _base64.b64encode(bytes(self)).decode()
    
    def __bytes__(self) -> bytes:
        return self._image.write_to_buffer('.png')                          #type:ignore
    
    def get_width(self) -> int:
        return self._image.width                                            #type:ignore
    
    def get_height(self) -> int:
        return self._image.height                                            #type:ignore
    
    def get_size(self) -> tuple[int, int]:
        return self.get_width(), self.get_height()
    
    def resize(self, width: int, height: int) -> 'Image':
        image = self._image

        image_width: int = image.width                                      #type:ignore
        image_height: int = image.height                                    #type:ignore

        resize_factor = min(256 / image_width, 256 / image_height)

        resized_image = image.resize(resize_factor)                         #type:ignore
        
        new_width: int = width                                              #type:ignore
        new_height: int = height                                            #type:ignore

        left = (new_width - 256) // 2
        top = (new_height - 256) // 2

        cropped_image = resized_image.crop(left, top, 256, 256)             #type:ignore

        return Image(cropped_image)
    
    def copy(self) -> 'Image':
        return self._image.copy()                                           #type:ignore
