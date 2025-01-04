import json

def load_json(file_path: str):
    with open(file_path, 'r') as file:
        return json.load(file)
    
def write_json(file_path: str, objs):
    json_obj: str = json.dumps(objs)
    with open(file_path, "w") as file:
        file.write(json_obj)