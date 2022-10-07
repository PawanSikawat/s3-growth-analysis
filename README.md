# s3-growth-analysis
Analyse the size of the buckets in your account and get the list of top growth buckets

# IMPORTANT: Version-2
- A version 2 of the code is released to develop branch. 
- This version shows a intuitive Progress Bar in terminal while running for Bucket Metadata and Storage Metrics steps.
- It also uses multi-threading under the hood for the Bucket Metadata and Storage Metrics steps resulting in ~25x speed.


# Run Command
python3 main.py

# Description of input_configs
**through_profile**: Creates boto3 session through profile. If set to False, it will look for aws creds in the environment variable - AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN <br />
**profile_name**: Name of the profile which will be used to create boto3 session if through_profile is set to True. If set to null, default profile will be used. <br />
**only_standard_storage**: If set to True, only StandardStorage will be counted towards size calculation. <br />
**all_storage_types**: If set to True, all different types of S3 Storages will be counted towards size calculation. It works only if only_standard_storage is set to False. <br />
**custom_storage_types**: List of S3 StorageTypes that should be counted towards size calculation. It works only if only_standard_storage and all_storage_types is set to False. <br />
**use_cached**: if set to True, existing files (bucket_metrics.json & top_growth_buckets.json) will be used to generate outcome. <br />

# Flow of code
1. All buckets within an account are fetched using S3 boto3 client buckets.all().
1. The region for each bucket is fetched using head_bucket().
   1. Retries are added using @retry annonation to handle unexpected failures.
   1. On getting ClientError expection, the bucket is set to be inaccessible through the used credentials and region is set to None.
   1. Region is retrieved from ['ResponseMetadata']['HTTPHeaders']['x-amz-bucket-region'] to handle null value sent for us-east.
1. The tags for each bucket is retrieved from Tagging().tag_set sub-resource.
1. Storage metrics and monthly growth is set for each bucket.
   1. A pool of Cloudwatch boto3 clients are created of each region for which a bucket is present. This is done to prohibit re-creation of clients for the same region.
   1. For each storage type passed, BucketSizeBytes is fetched between (today-2, today) and (today-32, today-30).
   1. If no Datapoint is present for a time-period or storage-type, 0.0 BucketSizeBytes is assumed.
   1. BucketSizeBytes for each storage type is summed up and used to set CurrentSize and MonthlyGrowth.
1. A sorted list on MonthlyGrowth is fetched to calculate Top Growth Buckets.
1. The objects list is cached to bucket_metrics.json and top_growth_buckets.json respectively.
1. The result is displayed on Terminal using rich.table.Table and the terminal output is stored in console_log.html file.

