from .images import *

import pyvips as _pyvips

class ImagesTranslationKeeper():
    def __init__(self):
        self._images: list[tuple[bytes, _pyvips.Image]] = []
        self._str_decodes: dict[str, bytes] =  {}
    
    def saveImageTranslation(self, bytes: bytes, image: _pyvips.Image) -> None:
        self._images.append((bytes, image))
    
    def hasImageTranslation(self, bytes: bytes) -> bool:
        for element in self._images:
            if element[0] == bytes:
                return True
        
        return False
    
    def hasStrDecode(self, data: str) -> bool:
        return data in self._str_decodes
    
    def getImageTranslation(self, bytes: bytes) -> _pyvips.Image:
        for element in self._images:
            if element[0] == bytes:
                return element[1]
            
        raise KeyError("no image found for this chain")
    
    def saveStrDecode(self, data: str, bytes: bytes) -> None:
        self._str_decodes[data] = bytes
    
    def getImageTranslationFromString(self, data: str) -> _pyvips.Image:
        if not data in self._str_decodes:
            raise KeyError("no decode found for this data")
        
        return self.getImageTranslation(self._str_decodes[data])
    
    def decodeStr(self, data: str) -> bytes:
        return self._str_decodes[data]

DEFAULT_TRANSLATION_KEEPER = ImagesTranslationKeeper()
