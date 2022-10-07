import os
import boto3
import botocore
from typing import Union
from retry import retry
from rich.progress import track
from datetime import datetime, timedelta
from model import Accessibility, AwsCreds, BucketMetrics



def create_session(through_profile: bool=True, profile: Union[str, None]=None, region: Union[str, None]=None) -> boto3.Session:
    # creates boto3 session through profile or through environment variables
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
    # checks the success for AWS Rest API calls made through boto3
    return 200 <= response.get('ResponseMetadata', {}).get('HTTPStatusCode', 400) < 300


@retry(StopIteration, tries=3, delay=2)
def get_bucket_location(s3, bucket_name: str) -> Union[str, None]:
    # fetches the region for a bucket
    try:
        response = s3.head_bucket(Bucket=bucket_name)
    except botocore.exceptions.ClientError:
        return
    if not check_success(response):
        raise StopIteration
    return response['ResponseMetadata']['HTTPHeaders']['x-amz-bucket-region']


def get_bucket_tags(bucket, region) -> Union[list[dict], None]:
    # fetches the TagSet for a bucket
    try:
        return None if region is None else bucket.Tagging().tag_set
    except botocore.exceptions.ClientError:
        return []


def get_bucket_metrics(session: boto3.Session) -> list[BucketMetrics]:
    # generates a list of BucketMetrics (name, region, tags) objects for all available S3 buckets in the account
    s3_client = session.client('s3')
    buckets = session.resource('s3').buckets.all()
    bucket_metrics = []
    for bucket in track(buckets, description='Setting Bucket Metadata...'):
        region = get_bucket_location(s3_client, bucket.name)
        bucket_metrics.append(BucketMetrics(bucket.name, region, get_bucket_tags(bucket, region), Accessibility.get_accessibility(region)))
    return bucket_metrics


@retry((StopIteration, botocore.exceptions.ClientError), tries=3, delay=2)
def get_storage_metrics(cloudwatch: boto3.client, bucket_name: str, start_date: datetime, end_date: datetime, storage_type: str):
    # returns the storage metric of a bucket for a particular day and a particular storage type
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
    # returns the datapoint fetched or else returns 0.0 indicating there is no datapoint, hence no data in bucket
    return response['Datapoints'][-1]['Average'] if len(response['Datapoints']) else 0.0


def generate_cloudwatch_clients(through_profile: bool, profile_name: Union[str, None], bucket_metrics: list[BucketMetrics], clients: dict) -> None:
    # generates a list of cloudwatch client for all aws regions having a bucket in the account
    for bucket_metric in bucket_metrics:
        if bucket_metric.region is not None and bucket_metric.region not in clients:
            clients[bucket_metric.region] = create_session(through_profile, profile_name, bucket_metric.region).client('cloudwatch')


def set_bucket_size_and_growth(through_profile: bool, profile_name: Union[str, None], storage_types: list[str], bucket_metrics: list[BucketMetrics]) -> None:
    # takes a list of BucketMetrics objects and sets their size & growth metrics
    cloudwatch_clients =  dict()
    # generate a pool of cloudwatch clients for each region
    generate_cloudwatch_clients(through_profile, profile_name, bucket_metrics, cloudwatch_clients)
    today =  datetime.now()
    _2_days_prior, _30_days_prior, _32_days_prior = today - timedelta(days=2), today - timedelta(days=30), today - timedelta(days=32)
    
    for bucket_metric in track(bucket_metrics, description='Setting Storage Metrics...'):
        # if bucket region is None, that means bucket was inaccessible through the creds used
        if bucket_metric.region is None:
            continue
        current_size, prior_month_size = 0.0, 0.0
        # loops over all passed storage types and sums up the result
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
        # sets the object metrics using the summed up metrics
        bucket_metric.current_size, bucket_metric.monthly_growth = current_size, current_size - prior_month_size
    
    
    

