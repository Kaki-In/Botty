import interactions as _interactions
import saves as _saves
import time as _time

class SimplySleepCreatorFactory(_interactions.CreatorFactory[float, _interactions.Sleepy]):
    def build_from(self, directory: _saves.ResourcesDirectory) -> 'SimplySleepCreator':
        return SimplySleepCreator()

class SimplySleepCreator(_interactions.Creator[float, _interactions.Sleepy]):
    def _create_object_from(self, description: float) -> _interactions.Sleepy:
        time_from = _time.monotonic()

        while _time.monotonic() - time_from  < description:
            if self.should_interrupt:
                raise _interactions.InteractionInterruptionError()
            
            _time.sleep(0.01)

        return _interactions.Sleepy()

