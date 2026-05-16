import numpy as _np
import scipy.spatial.distance as _scipy_spatial_dist

class EmbeddingVector():
    def __init__(self, vector: _np.ndarray) -> None:
        self.__vector = vector

    @property
    def vector(self) -> _np.ndarray:
        return self.__vector
    
    @staticmethod
    def similarity_between(v1: 'EmbeddingVector', v2: 'EmbeddingVector') -> float:
        return 1 - _scipy_spatial_dist.cosine(v1.vector, v2.vector)

    