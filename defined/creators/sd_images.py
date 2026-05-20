import typing as _T

import interactions as _interactions
import local_utils.images as _local_utils_images
import saves as _saves
import httpx as _httpx
import requests as _requests

class _stable_diffusion_image_generation_face_configuration_file_object(_T.TypedDict):
    weight: float
    guidance_start: float
    guidance_end: float
    module: str
    model: str

class _stable_diffusion_image_generation_configuration_file_object(_T.TypedDict):
    stable_diffusion_url: str
    negative_prompt: str
    steps_count: int
    include_loras: dict[str, float]
    cfg_scale: float
    face: _stable_diffusion_image_generation_face_configuration_file_object

class StableDiffusionImageGeneratorConfiguration():
    def __init__(self, directory: _saves.ResourcesDirectory) -> None:
        self.__configuration_file = _saves.ConfigurationFile[_stable_diffusion_image_generation_configuration_file_object](directory.get_resource('config.json'), {
                'stable_diffusion_url': 'http://localhost:7860/sdapi/v1',
                'negative_prompt': 'ugly, tiling, poorly drawn hands, poorly drawn feet, poorly drawn face, out of frame, extra limbs, disfigured, deformed, body out of frame, blurry, bad anatomy, blurred, watermark, grainy, signature, cut off, draft',
                'steps_count': 20,
                'include_loras': {
                    'ip-adapter-faceid-plusv2_sd15_lora': 0.9
                },
                'cfg_scale': 7.0,
                'face': {
                    'weight': 0.9,
                    'guidance_start': 0.5,
                    'guidance_end': 1,
                    "module": 'InsightFace+CLIP-H (IPAdapter)',
                    "model": 'ip-adapter-faceid-plusv2_sd15 [6e14fc1a]'
                }
            })
        self.__face_asset = directory.get_resource('face.png')
    
    @property
    def configuration_file(self) -> _saves.ConfigurationFile:
        return self.__configuration_file
    
    @property
    def face_resource(self) -> _saves.ResourceFile:
        return self.__face_asset

class StableDiffusionImageGeneratorFactory(_interactions.CreatorFactory[_interactions.ImageSettings, _local_utils_images.Image]):
    def build_from(self, directory: _saves.ResourcesDirectory) -> _interactions.Creator[_interactions.ImageSettings, _local_utils_images.Image]:
        configuration = StableDiffusionImageGeneratorConfiguration(directory)

        return StableDiffusionImageGenerator(configuration.configuration_file.read_configuration(), _local_utils_images.long_from_bytes(configuration.face_resource.read_raw()) if configuration.face_resource.exists else None)

class StableDiffusionImageGenerator(_interactions.Creator[_interactions.ImageSettings, _local_utils_images.Image]):
    def __init__(self, base_configuration: _stable_diffusion_image_generation_configuration_file_object, face_image: _T.Optional[_local_utils_images.Image]) -> None:
        super().__init__()

        self.__base_configuration = base_configuration
        self.__face_image = face_image
        self.__current_client = _httpx.Client()

    def on_interruption(self) -> None:
        self.__current_client.close()

    def on_finish(self) -> None:
        _requests.post(self.__base_configuration["stable_diffusion_url"] + '/unload_checkpoint')

    def _create_object_from(self, description: _interactions.ImageSettings) -> _local_utils_images.Image:
        _requests.post(self.__base_configuration["stable_diffusion_url"] + '/reload_checkpoint')

        try:
            response = self.__current_client.post(
                self.__base_configuration['stable_diffusion_url'] + '/txt2img',
                json={
                    "prompt": description.prompt + ". " + ", ".join([f"<lora:{lora_key}:{lora_value}>" for lora_key, lora_value in self.__base_configuration['include_loras'].items()]),
                    "negative_prompt": self.__base_configuration["negative_prompt"],
                    "steps": self.__base_configuration['steps_count'],
                    "width": description.width,
                    "height": description.height,
                    "cfg_scale": self.__base_configuration['cfg_scale'],
                    "alwayson_scripts": {
                        "controlnet": {
                            "args": [
                                {
                                    "enabled": description.is_self_face and self.__face_image is not None,
                                    "module": self.__base_configuration['face']['module'],
                                    "model": self.__base_configuration['face']['model'],
                                    "weight": self.__base_configuration['face']['weight'],
                                    "image": str(self.__face_image),
                                    "resize_mode": 1,
                                    "lowvram": False,
                                    "processor_res": 512,
                                    "threshold_a": 0,
                                    "threshold_b": 0,
                                    "guidance_start": self.__base_configuration['face']['guidance_start'],
                                    "guidance_end": self.__base_configuration['face']['guidance_end'],
                                    "control_mode": 0,
                                    "pixel_perfect": False
                                }
                            ]
                        }
                    }
                },
                timeout=None
            )
        except _httpx.RemoteProtocolError:
            raise _interactions.InteractionInterruptionError()

        response.raise_for_status()
        data = response.json()

        assert "images" in data and len(data["images"]) > 0

        return _local_utils_images.long_from_string(data["images"][0])
