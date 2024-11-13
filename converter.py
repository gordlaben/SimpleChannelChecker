import json
import re
from icecream import ic
import os
import time
import fnmatch

# File paths
converting_folder = './playlist/converter'

playlist_channel_name_tag = os.getenv("CHANNEL_TAG", "tvg-name")

# Regex pattern to capture tvg-name
tvg_name_pattern = re.compile(fr'{playlist_channel_name_tag}="([^"]+)"')


# Check if the playlist folder exists, and create it if not
if not os.path.exists(converting_folder):
    os.makedirs(converting_folder)
    ic("Directory Converter created.")
else:
    ic("Directory Converter already exists.")


def convert_m3u_to_json(m3u_file_path):
    # Dictionary to store the parsed data
    channels = {}

    if os.path.exists(m3u_file_path):
        # Parse the .m3u file
        with open(m3u_file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            for i in range(len(lines)):
                line = lines[i].strip()
                if line.startswith("#EXTINF"):
                    # Extracting the tvg-name (channel name) using regex
                    tvg_name_match = tvg_name_pattern.search(line)
                    if tvg_name_match:
                        tvg_name = tvg_name_match.group(1)
                        # Step 1: Remove symbols (non-alphanumeric characters, except spaces)
                        no_symbols = re.sub(r'[^A-Za-z0-9 ]+', '', tvg_name)
                        # Step 2: Replace double spaces
                        with_hyphens = re.sub(r'\s+', '-', no_symbols)
                        # Step 3: Convert to lowercase
                        final_string = with_hyphens.lower()

                        # Get the URL which is the next line after #EXTINF
                        if i + 1 < len(lines):
                            url = lines[i + 1].strip()
                            # Append to channels dictionary
                            if final_string in channels:
                                channels[final_string].append(url)
                            else:
                                channels[final_string] = [url]

        # Export to JSON
        file_name_without_extension, _ = os.path.splitext(m3u_file_path)
        filename = file_name_without_extension + ".json"
        with open(filename, 'w', encoding='utf-8') as json_file:
            ic("Dumping JSON.")
            json.dump(channels, json_file, indent=2)

        if os.path.exists(filename):
            ic("Successfully converted.")

        if os.path.exists(m3u_file_path):
            os.remove(m3u_file_path)
            ic("Removing m3u file.")


def check_and_convert_files():
    global converting_folder
    while True:
        try:
            # Loop through all files in the specified directory
            for filename in os.listdir(converting_folder):
                # Check if the file has a .m3u or .m3u8 extension
                if fnmatch.fnmatch(filename, "*.m3u") or fnmatch.fnmatch(filename, "*.m3u8"):
                    # Construct the full file path
                    file_path = os.path.join(converting_folder, filename)
                    # Run the convert_to_json function on the file
                    convert_m3u_to_json(file_path)

            time.sleep(5)  # Check for changes every 5 seconds

        except KeyboardInterrupt:
            ic("-- Stopping file watcher.")
            break