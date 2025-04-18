'''
from results.json I want to count len(objects)
'''
import json

with open('scripts/results.json', 'r') as file:
    data = json.load(file)

print(len(data))
