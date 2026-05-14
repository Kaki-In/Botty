from .images import *
from .translations_keeper import *

import base64 as _base64
import asyncio as _asyncio
import pyvips as _pyvips

async def from_bytes(bytes: bytes) -> Image:
    return await _asyncio.get_event_loop().run_in_executor(None, long_from_bytes, bytes) #type:ignore

async def from_string(data: str) -> Image:
    return await _asyncio.get_event_loop().run_in_executor(None, long_from_string, data) #type:ignore

def long_from_bytes(bytes: bytes) -> Image:
    if DEFAULT_TRANSLATION_KEEPER.hasImageTranslation(bytes):
        image = DEFAULT_TRANSLATION_KEEPER.getImageTranslation(bytes)
    else:
        image: _pyvips.Image = _pyvips.Image.new_from_buffer(bytes, "") #type:ignore
        DEFAULT_TRANSLATION_KEEPER.saveImageTranslation(bytes, image)
    
    return Image(image)

def long_from_string(data: str) -> Image:
    if DEFAULT_TRANSLATION_KEEPER.hasStrDecode(data):
        bytes = DEFAULT_TRANSLATION_KEEPER.decodeStr(data)
    else:
        bytes = string_to_bytes(data)
        DEFAULT_TRANSLATION_KEEPER.saveStrDecode(data, bytes)

    return long_from_bytes(bytes)

def bytes_to_string(image_data: bytes) -> str:
    return _base64.b64encode(image_data).decode()

def string_to_bytes(image_data: str) -> bytes:
    return _base64.b64decode(image_data.encode())
