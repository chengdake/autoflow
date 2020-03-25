from autopipeline.pipeline.components.feature_engineer.encode.base import BaseEncoder

__all__ = ["LabelEncoder"]


class LabelEncoder(BaseEncoder):
    class__ = "LabelEncoder"
    module__ = "autopipeline.pipeline.proxy.label_encode"