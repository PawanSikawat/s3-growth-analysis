# s3_growth_analysis
Analyse the size of the buckets in your account and get the list of top growth buckets

# Run Command
python3 main.py

# Description of input_configs
**through_profile**: Creates boto3 session through profile. If set to False, it will look for aws creds in the environment variable - AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN <br />
**profile_name**: Name of the profile which will be used to create boto3 session if through_profile is set to True. If set to null, default profile will be used. <br />
**only_standard_storage**: If set to True, only StandardStorage will be counted towards size calculation. <br />
**all_storage_types**: If set to True, all different types of S3 Storages will be counted towards size calculation. It works only if only_standard_storage is set to False. <br />
**custom_storage_types**: List of S3 StorageTypes that should be counted towards size calculation. It works only if only_standard_storage and all_storage_types is set to False. <br />
**use_cached**: if set to True, existing files (bucket_metrics.json & top_growth_buckets.json) will be used to generate outcome. <br />

