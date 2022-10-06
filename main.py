import typer
from rich import console, traceback
import common_utils as cu
import file_utils as fu
from model import FileName, InputConfigs



app = typer.Typer()
console = console.Console(record=True)
traceback.install()


@app.command(short_help='Generate S3 Analysis')
def generate_analysis():
    # fetch the input configs
    input_configs = InputConfigs(fu.read_json(FileName.INPUT_CONFIGS))

    # if use_cached is True, use existing files to generate objects array
    if input_configs.use_cached:
        bucket_metrics = cu.read_as_object(FileName.BUCKET_METRICS)
        top_growth_buckets = cu.read_as_object(FileName.TOP_GROWTH_BUCKETS)
    # else formulate fresh objects by running the required operations
    else:
        # create objects with the buckets metadata - name, tags, region
        bucket_metrics = cu.create_bucket_metrics(input_configs.through_profile, input_configs.profile_name)
        # configure the storage metrics for the objects
        cu.configure_storage_metrics(input_configs.through_profile, input_configs.profile_name, cu.get_storage_type(input_configs), bucket_metrics)
        # filter the buckets with highest growth in last 30 days
        top_growth_buckets = cu.fetch_top_growth_buckets(bucket_metrics)
        # write the fresh objects to file
        cu.write_to_file(bucket_metrics, top_growth_buckets)
    # generate tables out of the objects
    cu.show_as_tables(bucket_metrics, top_growth_buckets, console)
    # save the console output to a html file
    console.save_html(FileName.CONSOLE_LOG)


if __name__=='__main__':
    app()








