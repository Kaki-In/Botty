from .creator import Creator
from .creator_factory import CreatorFactory

import saves as _saves
import typing as _T

class CreatorsState():
    def __init__(self) -> None:
        self.__current_creators: list[Creator] = []

    @property
    def current_creators(self) -> _T.Sequence[Creator]:
        return self.__current_creators
    
    def create_from_factory[T1, T2](self, factory: CreatorFactory[T1, T2], data: T1, directory: _saves.ResourcesDirectory) -> T2:
        creator = factory.build_from(directory)
        self.__current_creators.append(creator)

        try:
            return creator.create_object_from(data)
        finally:
            self.__current_creators.remove(creator)

    def interrupt_all(self) -> None:
        for creator in self.__current_creators:
            creator.interrupt()

