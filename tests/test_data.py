'''
from results.json I want to count len(objects)
'''
import os
import sys
import json

# adjust path to import from parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


DATA_PATH: str = 'scripts/results.json'


if __name__ == "__main__":
    with open(DATA_PATH, 'r') as file:
        data = json.load(file)

    print(len(data))
