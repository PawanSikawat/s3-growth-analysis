import humanize
import json
from rich import console, table
from typing import Union
import boto3_utils as bu
import file_utils as fu
from constant import TOP_GROWTH_BUCKETS_COUNT
from model import BucketMetrics, FileName, InputConfigs, S3StorageTypes



def read_as_object(file_name: str) -> list[BucketMetrics]:
    # read a json array file and convert jsons into BucketMetrics objects
    return [BucketMetrics(m['name'], m['region'], m['tags'], m['accessible'], m['current_size'], m['monthly_growth']) for m in fu.read_json(file_name)]


def write_as_json(bucket_metrics: list[BucketMetrics], file_name: str) -> None:
    # convert BucketMetrics objects into dictionary and write it back to a file
    fu.write_json([bucket_metric.__dict__ for bucket_metric in bucket_metrics], file_name)


def create_bucket_metrics(through_profile: bool, profile_name: Union[str, None]) -> list[BucketMetrics]:
    # creates a boto3 session and fetches bucket metrics (name, region, tags) through it
    return bu.get_bucket_metrics(bu.create_session(through_profile=through_profile, profile=profile_name))


def configure_storage_metrics(through_profile: bool, profile_name: Union[str, None], storage_types: list[str], bucket_metrics: list[BucketMetrics]) -> None:
    # takes a list of BucketMetrics objects and sets their bucket size & growth
    bu.set_bucket_size_and_growth(through_profile, profile_name, storage_types, bucket_metrics)


def fetch_top_growth_buckets(bucket_metrics: list[BucketMetrics]) -> list[BucketMetrics]:
    # returns a top X sorted list of BucketMetrics sorted on monthly_growth
    return sorted(bucket_metrics, key=lambda k: k.monthly_growth, reverse=True)[:min(len(bucket_metrics), TOP_GROWTH_BUCKETS_COUNT)]


def get_storage_type(input_configs: InputConfigs) -> list[str]:
    # only_standard_storage > all_storage_types > custom_storage_types
    if input_configs.only_standard_storage:
        return S3StorageTypes.STANDARD_STORAGE
    elif input_configs.all_storage_types:
        return S3StorageTypes.ALL_STORAGE_TYPES
    else:
        return input_configs.custom_storage_types


def write_to_file(bucket_metrics: list[BucketMetrics], top_growth_buckets: list[BucketMetrics]) -> None:
    # writes bucket_metrics & top_growth_buckets to json file
    write_as_json(bucket_metrics, FileName.BUCKET_METRICS)
    write_as_json(top_growth_buckets, FileName.TOP_GROWTH_BUCKETS)


def transform_tags(tags: list[dict]) -> Union[dict, None]:
    # transforms default TagSet structure into a dictionary
    if tags:
        transformed_tags = {}
        for tag in tags:
            transformed_tags[tag['Key']] = tag['Value']
        return json.dumps(transformed_tags)


def get_metrics_table() -> table.Table:
    # generates table structure for 'Bucket Metrics'
    metrics_table = table.Table(title='Bucket Metrics', header_style='bold blue', border_style='bold cyan')
    metrics_table.add_column('#', style='dim', width=6)
    metrics_table.add_column('Bucket', min_width=20, style='red', no_wrap=True)
    metrics_table.add_column('Region', min_width=10, style='magenta')
    metrics_table.add_column('Tags', min_width=20, style='green')
    metrics_table.add_column('Size', min_width=10, justify='right', style='cyan')
    metrics_table.add_column('Accessible', min_width=6, justify='center')
    return metrics_table


def get_growth_table() -> table.Table:
    # generates table structure for 'Top Growth Buckets'
    growth_table = table.Table(title='Top Growth Buckets', header_style='bold blue', border_style='bold cyan')
    growth_table.add_column('#', style='dim', width=6)
    growth_table.add_column('Bucket', min_width=20, style='red')
    growth_table.add_column('Size Growth', min_width=20, justify='right', style='magenta')
    return growth_table


def show_as_tables(bucket_metrics: list[BucketMetrics], top_growth_buckets: list[BucketMetrics], console: console.Console) -> None:
    # creates Tables out of bucket_metrics & top_growth_buckets and displays it on console
    metrics_table = get_metrics_table()
    growth_table = get_growth_table()
    for idx, metric in enumerate(bucket_metrics, start=1):
        metrics_table.add_row(str(idx), metric.name, metric.region, transform_tags(metric.tags), humanize.naturalsize(metric.current_size), metric.accessible)
    for idx, growth in enumerate(top_growth_buckets, start=1):
        growth_table.add_row(str(idx), growth.name, humanize.naturalsize(growth.monthly_growth))
    console.print(metrics_table)
    console.print(growth_table)