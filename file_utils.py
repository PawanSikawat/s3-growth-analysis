import json
from typing import Union


def read_json(file_name) -> dict:
    # opens a json file and returns a json object of it
    f = open(file_name)
    return json.load(f)


def write_json(data: Union[dict, list[dict]], file_name: str) -> None:
    # writes a dict or dict array into a json file
    json_obj = json.dumps(data)
    with open(file_name, "w") as outfile:
        outfile.write(json_obj)
    outfile.close()