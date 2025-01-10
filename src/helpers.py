import json
import datetime

def load_json(file_path: str):
    with open(file_path, 'r') as file:
        return json.load(file)
    
def write_json(file_path: str, objs):
    json_obj: str = json.dumps(objs)
    with open(file_path, "w") as file:
        file.write(json_obj)

def is_date_valid(day: int, month: int, year: int) -> bool:
    try:
        datetime.date(year, month, day)
        return True
    except ValueError:
        return False