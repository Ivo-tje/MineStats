#!/bin/python3
import os
import json

# Directory containing JSON files
directory = "/opt/minecraft/world/stats"

output_data = {}

for filename in os.listdir(directory):
    if filename.endswith(".json"):
        filepath = os.path.join(directory, filename)
        with open(filepath, "r", encoding="utf-8") as file:
            try:
                data = json.load(file)
                userid = {"userid": os.path.splitext(filename)[0]}
                output_data[os.path.splitext(filename)[0]] = data

            except json.JSONDecodeError as e:
                print(f"Error reading {filename}: {e}")

print(json.dumps(output_data, indent=4))
