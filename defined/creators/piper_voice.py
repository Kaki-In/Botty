import typing as _T

import interactions as _interactions
import piper as _piper
import os as _os
import pydub as _pydub
import saves as _saves

class _piper_voice_configuration_object(_T.TypedDict):
    voicename: str
    speaker_id: int
    length_scale: float | None
    noise_scale: float | None
    noise_w_scale: float | None
    normalize_audio: bool
    volume: float

class PiperVoiceFactory(_interactions.CreatorFactory[str, _pydub.AudioSegment]):
    def build_from(self, directory: _saves.ResourcesDirectory) -> 'PiperVoice':
        config = _saves.ConfigurationFile[_piper_voice_configuration_object](directory.get_resource('config.json'), {
                'voicename': '',
                'speaker_id': 0,
                'length_scale': None,
                'noise_scale': None,
                'noise_w_scale': None,
                'normalize_audio': False,
                'volume': 1
            }).read_configuration()

        return PiperVoice(config['voicename'], _piper.SynthesisConfig(
            speaker_id = config['speaker_id'],
            length_scale = config['length_scale'],
            noise_scale = config['noise_scale'],
            noise_w_scale = config['noise_w_scale'],
            normalize_audio = config['normalize_audio'],
            volume = config['volume']
        ))

class PiperVoice(_interactions.Creator[str, _pydub.AudioSegment]):
    def __init__(self, voicename: str, configuration: _piper.SynthesisConfig) -> None:
        super().__init__()

        self.__config = configuration
        self.__voice = _piper.PiperVoice.load(voicename, download_dir=_os.path.abspath('./data/piper/'))

    def _create_object_from(self, description: str) -> _pydub.AudioSegment:
        total_bytes = b''
        
        for chunk in self.__voice.synthesize(description, self.__config):
            self.raise_interruption_if_needed()
            total_bytes += chunk.audio_int16_bytes
        
        return _pydub.AudioSegment(total_bytes, channels=1, sample_width=2, frame_rate=self.__voice.config.sample_rate)


