import numpy as _np
import scipy.spatial.distance as _scipy_spatial_dist
import typing as _T

class EmbeddingVector():
    def __init__(self, vector: _np.ndarray) -> None:
        self.__vector = vector

    @property
    def vector(self) -> _np.ndarray:
        return self.__vector
    
    @staticmethod
    def similarity_between(v1: 'EmbeddingVector', v2: 'EmbeddingVector') -> float:
        return 1 - _scipy_spatial_dist.cosine(v1.vector, v2.vector)
    
    @classmethod
    def from_list(cls, l: _T.Sequence[float]) -> _T.Self:
        return cls(_np.array(l))
    
    def as_list(self) -> _T.Sequence[float]:
        return self.__vector.tolist()

    