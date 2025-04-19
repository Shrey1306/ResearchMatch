'''
from results.json I want to count len(objects)
'''
import json

with open('results.json', 'r') as file:
    data = json.load(file)

print(len(data))
