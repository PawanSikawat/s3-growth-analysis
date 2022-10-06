from typing import Union


class StaticClass:
    def __new__(cls):
        raise TypeError(f"{cls.__name__} is static. It cannot be instantiated!")


class Accessibility(StaticClass):
    accessible = ':white_check_mark:'
    inaccessible = ':x:'

    @classmethod
    def get_accessibility(cls, input=None):
        return cls.accessible if input is not None else cls.inaccessible 


class AwsCreds(StaticClass):
    ACCESS_KEY = 'AWS_ACCESS_KEY_ID'
    SECRET_KEY = 'AWS_SECRET_ACCESS_KEY'
    SESSION_TOKEN = 'AWS_SESSION_TOKEN'


class BucketMetrics:
    def __init__(self, name: str, region: Union[str, None], tags: Union[list, None], accessible: str, current_size: float=0.0, monthly_growth: float=0.0):
        self.name = name
        self.region = region
        self.tags = tags
        self.accessible = accessible
        self.current_size = current_size
        self.monthly_growth = monthly_growth


class FileName(StaticClass):
    BUCKET_METRICS = 'bucket_metrics.json'
    CONSOLE_LOG = 'console_log.html'
    INPUT_CONFIGS = 'input_configs.json'
    TOP_GROWTH_BUCKETS = 'top_growth_buckets.json'


class InputConfigs(object):
    def __init__(self, dictionary):
        for key in dictionary:
            setattr(self, key, dictionary[key])


class S3StorageTypes(StaticClass):
    STANDARD_STORAGE = ['StandardStorage']
    ALL_STORAGE_TYPES = [
        'StandardStorage', 'IntelligentTieringFAStorage', 'IntelligentTieringIAStorage', 'IntelligentTieringAAStorage', 
        'IntelligentTieringAIAStorage', 'IntelligentTieringDAAStorage', 'StandardIAStorage', 'StandardIASizeOverhead', 
        'StandardIAObjectOverhead', 'OneZoneIAStorage', 'OneZoneIASizeOverhead', 'ReducedRedundancyStorage', 
        'GlacierInstantRetrievalSizeOverhead', 'GlacierInstantRetrievalStorage', 'GlacierStorage', 'GlacierStagingStorage', 
        'GlacierObjectOverhead', 'GlacierS3ObjectOverhead', 'DeepArchiveStorage', 'DeepArchiveObjectOverhead', 
        'DeepArchiveS3ObjectOverhead', 'DeepArchiveStagingStorage'
    ]