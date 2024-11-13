from flask import Flask, redirect, abort, send_file
import json
import os
import subprocess
import time
import threading

app = Flask(__name__)

# Clean Provider Base URL, check for protocol correction and remove trailing slash if exists
def clean_url(url):
    print(url)
    # Check if the URL is None
    if url is None:
        raise ValueError("URL cannot be None")

    # Check if URL starts with "http://" or "https://"
    if url.startswith("http://") or url.startswith("https://"):
        # Remove the trailing slash if it exists
        if url.endswith("/"):
            url = url[:-1]
        return url
    else:
        raise ValueError("URL must start with http:// or https://")


# Retrieve environment variables for configurations, with default values if not set
provider_base_url = os.getenv("PROVIDER_BASE_URL")
provider_base_url = clean_url(provider_base_url)
protocol = os.getenv("WEB_PROTOCOL", "http")
server_hostname = os.getenv("WEB_HOSTNAME", "127.0.0.1")
scc_port = os.getenv("SCC_PORT", "80")
scc_playlist_port = os.getenv("SCC_PLAYLIST_PORT")
flask_host = os.getenv("FLASK_HOST", "0.0.0.0")
flask_debug = os.getenv("FLASK_DEBUG", "True")

# Define M3U playlist file name (default: "playlist.m3u")
m3u_filename = os.getenv("PLAYLIST_NAME", "playlist.m3u")

# Define the path for the playlist folder and playlist file
playlist_folder = "./playlist"
playlist_path = playlist_folder + "/playlist.json"


# Check if the playlist folder exists, and create it if not
if not os.path.exists(playlist_folder):
    os.makedirs(playlist_folder)
    print(f"Directory '{playlist_folder}' created.")
else:
    print(f"Directory '{playlist_folder}' already exists.")

# Function to check for existence of 'playlist.json', and create it with initial data if missing
def check_or_create_playlist():
    file_path = "./playlist/playlist.json"

    # Initial data for the playlist if the file doesn't exist
    initial_data = {
        "tester": [
            "OMG1337",
            "OMG1338"
        ]
    }

    # Create and write the initial data if 'playlist.json' does not exist
    if not os.path.isfile(file_path):
        with open(file_path, "w") as file:
            json.dump(initial_data, file, indent=2)
        print("playlist.json file created with initial data.")
    else:
        print("playlist.json already exists.")


# Function to generate the M3U playlist file based on the URL map
def generate_playlist(url_map):
    # Delete the existing M3U file if it exists
    if os.path.exists(m3u_filename):
        os.remove(m3u_filename)
        print(f"{m3u_filename} already exists. Deleting it.")

    # Write to the new M3U file
    with open(m3u_filename, "w") as m3u_file:
        m3u_file.write("#EXTM3U\n")  # Optional M3U header for extended format

        # Write each entry from the URL map to the M3U file
        for value in url_map.items():
            # Construct the playlist URL with or without a specific port
            if scc_playlist_port:
                playlist_url = str(protocol + "://" + server_hostname + ":" + scc_playlist_port + "/proxy/" + value[0])
            else:
                playlist_url = str(protocol + "://" + server_hostname + "/proxy/" + value[0])

            # Default duration (-1 for unknown) and title (extracted from URL)
            duration = -1
            title = os.path.basename(playlist_url)
            m3u_file.write(f"#EXTINF:{duration},{title}\n")
            m3u_file.write(playlist_url + "\n")  # Write the actual URL

    print("Playlist Generated.")


# Function to watch for changes in 'playlist.json' and regenerate the M3U file if updated
def check_for_changes():
    global last_modified_time, url_map
    while True:
        try:
            # Check the modification time of 'playlist.json'
            current_modified_time = os.path.getmtime(playlist_path)
            if current_modified_time != last_modified_time:
                print("Detected change in playlist.json. Regenerating playlist.")
                last_modified_time = current_modified_time

                # Reload the updated URL map and regenerate the M3U playlist
                with open(playlist_path, 'r') as file:
                    url_map = json.load(file)
                generate_playlist(url_map)

            time.sleep(5)  # Check for changes every 5 seconds
        except KeyboardInterrupt:
            print("Stopping file watcher.")
            break

# Function to check if a stream is active using FFmpeg to read data from it
def is_stream_active_ffmpeg(url):
    try:
        # Run FFmpeg to try to read a few seconds from the stream
        result = subprocess.run(
            ["ffmpeg", "-i", url, "-t", "5", "-f", "null", "-"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=15
        )

        # Check for specific error messages in FFmpeg output indicating inactivity
        if "Input/output error" in result.stderr.decode():
            print("Stream is inactive.")
            return False
        else:
            print("Stream is active.")
            return True
    except subprocess.TimeoutExpired:
        print("FFmpeg timed out. Stream might be inactive or unreachable.")
        return False

# Function to find and return an active stream URL for a given path name
def loop_through(url_map, path_name):
    # Check if path_name exists in url_map
    if path_name not in url_map:
        print(f"Error: '{path_name}' not found in playlist.json")
        return None  # or handle as you see fit, e.g., return a custom error value

    for channel_id in url_map[path_name]:  # Loop through the list of URLs for the path
        stream_url = provider_base_url + "/" + channel_id
        # Uncomment 'is_stream_alive' to check if the stream is reachable
        # if is_stream_alive(value):
        if is_stream_active_ffmpeg(stream_url):  # Check if the stream is active
            return channel_id

    return None  # Return None if no active stream is found


# Initialize the playlist file and load URL mappings
print("Step #1 - Check or Create playlist.json")
check_or_create_playlist()

print("Step #2 - Create url_map out of playlist.json file")
last_modified_time = os.path.getmtime(playlist_path)
with open(playlist_path, 'r') as file:
    url_map = json.load(file)

print("Step #3 - Generate playlist.m3u")
generate_playlist(url_map)


# Flask route to serve the M3U playlist file
@app.route('/playlist.m3u')
def serve_playlist():
    return send_file('playlist.m3u', mimetype="audio/x-mpegurl")


# Flask route to proxy requests for a specific stream path
@app.route('/proxy/<path_name>')
def proxy(path_name):
    channel_id = loop_through(url_map, path_name)  # Find an active stream URL
    if channel_id is not None:
        stream_final_url = provider_base_url + "/" + channel_id
        return redirect(stream_final_url, code=302)  # Redirect to the active stream
    else:
        abort(404, description="URL not found")  # Return 404 if no URL is found

# Entry point for the script to start the file-watcher thread and run the Flask app
if __name__ == '__main__':
    threading.Thread(target=check_for_changes, daemon=True).start()  # Start file-watcher thread
    app.run(host=flask_host, port=scc_port, debug=flask_debug)  # Run Flask app with specified host and port