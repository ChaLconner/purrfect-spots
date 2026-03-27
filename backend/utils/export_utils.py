import csv
import io
import json
from typing import Any, List

def data_to_csv(data: List[dict[str, Any]], fieldnames: List[str] | None = None) -> str:
    """
    Convert a list of dictionaries to a CSV string.
    """
    if not data:
        return ""
    
    if not fieldnames:
        fieldnames = list(data[0].keys())
        
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for row in data:
        # Flatten nested dicts for CSV if necessary
        flat_row = {}
        for k, v in row.items():
            if isinstance(v, (dict, list)):
                flat_row[k] = json.dumps(v)
            else:
                flat_row[k] = v
        writer.writerow(flat_row)
        
    return output.getvalue()

def data_to_json(data: List[dict[str, Any]]) -> str:
    """
    Convert a list of dictionaries to a JSON string.
    """
    return json.dumps(data, indent=2, default=str)
