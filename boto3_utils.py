import os
import boto3
import botocore
from typing import Union
from retry import retry
from datetime import datetime, timedelta
from model import Accessibility, AwsCreds, BucketMetrics



def create_session(through_profile: bool=True, profile: Union[str, None]=None, region: Union[str, None]=None) -> boto3.Session:
    if through_profile:
        return boto3.Session(profile_name=profile, region_name=region)
    else:
        return boto3.Session(
            aws_access_key_id=os.getenv(AwsCreds.ACCESS_KEY),
            aws_secret_access_key=os.getenv(AwsCreds.SECRET_KEY),
            aws_session_token=os.getenv(AwsCreds.SESSION_TOKEN),
            region_name=region
        )


def check_success(response: dict) -> bool:
    return 200 <= response.get('ResponseMetadata', {}).get('HTTPStatusCode', 400) < 300


@retry(StopIteration, tries=3, delay=2)
def get_bucket_location(s3, bucket_name: str) -> Union[str, None]:
    try:
        response = s3.head_bucket(Bucket=bucket_name)
    except botocore.exceptions.ClientError:
        return
    if not check_success(response):
        raise StopIteration
    return response['ResponseMetadata']['HTTPHeaders']['x-amz-bucket-region']


def get_bucket_tags(bucket, region) -> Union[list[dict], None]:
    try:
        return None if region is None else bucket.Tagging().tag_set
    except botocore.exceptions.ClientError:
        return []


def get_bucket_metrics(session: boto3.Session) -> list[BucketMetrics]:
    s3_client = session.client('s3')
    buckets = session.resource('s3').buckets.all()
    bucket_metrics = []
    for bucket in buckets:
        region = get_bucket_location(s3_client, bucket.name)
        bucket_metrics.append(BucketMetrics(bucket.name, region, get_bucket_tags(bucket, region), Accessibility.get_accessibility(region)))
    return bucket_metrics


@retry((StopIteration, botocore.exceptions.ClientError), tries=3, delay=2)
def get_storage_metrics(cloudwatch: boto3.client, bucket_name: str, start_date: datetime, end_date: datetime, storage_type: str):
    try:
        response = cloudwatch.get_metric_statistics(
            Namespace="AWS/S3",
            MetricName="BucketSizeBytes",
            Dimensions=[
                {
                    "Name": "BucketName",
                    "Value": bucket_name
                },
                {
                    "Name": "StorageType",
                    "Value": storage_type
                }
            ],
            StartTime=start_date,
            EndTime=end_date,
            Period=86400,
            Statistics=['Average']
        )
    except botocore.exceptions.ClientError:
        raise
    if not check_success(response):
        raise StopIteration
    return response['Datapoints'][-1]['Average'] if len(response['Datapoints']) else 0.0


def generate_cloudwatch_clients(through_profile: bool, profile_name: Union[str, None], bucket_metrics: list[BucketMetrics], clients: dict) -> None:
    for bucket_metric in bucket_metrics:
        if bucket_metric.region is not None and bucket_metric.region not in clients:
            clients[bucket_metric.region] = create_session(through_profile, profile_name, bucket_metric.region).client('cloudwatch')


def set_bucket_size_and_growth(through_profile: bool, profile_name: Union[str, None], storage_types: list[str], bucket_metrics: list[BucketMetrics]) -> None:
    cloudwatch_clients =  dict()
    generate_cloudwatch_clients(through_profile, profile_name, bucket_metrics, cloudwatch_clients)
    today =  datetime.now()
    _2_days_prior, _30_days_prior, _32_days_prior = today - timedelta(days=2), today - timedelta(days=30), today - timedelta(days=32)
    for bucket_metric in bucket_metrics:
        if bucket_metric.region is None:
            continue
        current_size, prior_month_size = 0.0, 0.0
        for storage_type in storage_types:
            try:
                current_size += get_storage_metrics(
                    cloudwatch_clients[bucket_metric.region], bucket_metric.name, _2_days_prior, today, storage_type
                )
                prior_month_size += get_storage_metrics(
                    cloudwatch_clients[bucket_metric.region], bucket_metric.name, _32_days_prior, _30_days_prior, storage_type
                )
            except:
                print(f"Couldn't set storage metrics for: {bucket_metric.name} and storage type: {storage_type}")
        bucket_metric.current_size, bucket_metric.monthly_growth = current_size, current_size - prior_month_size
    
    
    

