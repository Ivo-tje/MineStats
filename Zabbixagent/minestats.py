#!/bin/python3
import os
import sys
import json
from mcrcon import MCRcon


###sys.argv[1] - Host/ip
###sys.argv[2] - port
###sys.argv[3] - password

# Directory containing JSON files
directory = "/opt/minecraft/world/stats"

output_data = {}

def send_minecraft_save():
    RCON_HOST = sys.argv[1]
    RCON_PORT = sys.argv[2]
    RCON_PASSWORD = sys.argv[3]

    try:
        with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
            mcr.command("save-all")
    except Exception:
        pass  # Ignore errors while saving

send_minecraft_save(); # Save stats

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
