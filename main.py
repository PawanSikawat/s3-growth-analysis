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
    input_configs = InputConfigs(fu.read_json(FileName.INPUT_CONFIGS))
    if input_configs.use_cached:
        bucket_metrics = cu.read_as_object(FileName.BUCKET_METRICS)
        top_growth_buckets = cu.read_as_object(FileName.TOP_GROWTH_BUCKETS)
    else:
        bucket_metrics = cu.create_bucket_metrics(input_configs.through_profile, input_configs.profile_name)
        cu.configure_storage_metrics(input_configs.through_profile, input_configs.profile_name, cu.get_storage_type(input_configs), bucket_metrics)
        top_growth_buckets = cu.fetch_top_growth_buckets(bucket_metrics)
        cu.write_to_file(bucket_metrics, top_growth_buckets)
    cu.show_as_tables(bucket_metrics, top_growth_buckets, console)
    console.save_html(FileName.CONSOLE_LOG)


if __name__=='__main__':
    app()








