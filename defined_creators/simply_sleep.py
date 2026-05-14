from interactions import Creator, CreatorFactory, InteractionInterruptionError
from defined_creators.used_objects import Sleepy

from saves.directory import ResourcesDirectory

import time as _time

class SimplySleepCreatorFactory(CreatorFactory[float, Sleepy]):
    def build_from(self, directory: ResourcesDirectory) -> 'SimplySleepCreator':
        return SimplySleepCreator()

class SimplySleepCreator(Creator[float, Sleepy]):
    def _create_object_from(self, description: float) -> Sleepy:
        time_from = _time.monotonic()

        while _time.monotonic() - time_from  < description:
            if self.should_interrupt:
                raise InteractionInterruptionError()
            
            _time.sleep(0.01)

        return Sleepy()

