
# Simple Channel Checker (SCC)

**Simple Channel Checker (SCC)** is a tool designed to streamline online streaming experiences by managing multiple stream sources for a single channel. SCC can designate a primary stream, with additional streams as fallbacks in case of failure, ensuring seamless playback for live or online channels.

<br />

## Quick Start with Docker

Use the provided `docker-compose.yml` file to get started quickly:

```bash
docker compose up -d
```

On startup, SCC creates a directory named `scc` and generates a sample `playlist.json` file for testing purposes.

Example `playlist.json`:

```json
{
    "us-channel-name": [
         "channel-id-or-url-1",
         "channel-id-or-url-2"
     ]
}
```

- **`us-channel-name`**: Represents the channel or station **name**.
- **`channel-id-1`**: Represents the PRIMARY unique **ID** for the channel or station within the provider's API.
- **`channel-id-2`**: Represents the FALLBACK unique **ID** for the channel or station within the provider's API.

<br />

## m3u to JSON Converter

I’ve created a converter function to streamline your workflow. In your main directory, you’ll find a folder named playlist/converter. Simply drop your .m3u or .m3u8 playlist files into this folder, and within a few seconds, they will be converted into .json format.
Please note that the converter does not merge channels; it performs a direct format conversion only. You’ll still need to handle any main and backup channel configurations manually.

And as already mentioned, from that json file, remove your PROVIDER URL which is added as a ENV variable.

<br />

## Docker Compose Configuration

SCC is packaged as a Docker service and includes [Dozzle](https://github.com/amir20/dozzle) for real-time log viewing. Here’s an overview of the services:

```yaml
services:
    simplechannelchecker:
        container_name: simplechannelchecker
        image: gordlaben/simplechannelchecker:latest
        ports:
            - 1337:80
        environment:
            - SCC_PLAYLIST_PORT=1337 # change this - The port used for playlist proxying.
            - WEB_HOSTNAME=127.0.0.1 # change this - The public IP address or domain name for accessing SCC.
        command: [ "python", "/app/main.py" ]
        volumes:
            - ./scc:/app/playlist
        restart: always

    dozzle:
        container_name: dozzle
        image: amir20/dozzle:latest
        #environment: # Visit to see how to add users.yml file to /dozzle/data folder https://dozzle.dev/guide/authentication#file-based-user-management
            #- DOZZLE_AUTH_PROVIDER=simple
            #- DOZZLE_AUTH_TTL=48h
        volumes:
            - /var/run/docker.sock:/var/run/docker.sock
            - ./dozzle/data:/data
        ports:
            - 3333:8080
        restart: unless-stopped
```

<br />

## Environment Variables

| Variable            | Default        | Description                                                                                                                                                                                     |
|---------------------|----------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `PROVIDER_BASE_URL` | `None`         | The base URL of the stream provider’s API (e.g., `http://api.providerurl.com/xxxxx/yyyyy`). If NONE, it will take full URLs from the .json file. Do **not** include the channel ID in this URL. |
| `WEB_PROTOCOL`      | `http`         | Protocol for accessing the streams (`http` or `https`).                                                                                                                                         |
| `WEB_HOSTNAME`      | `127.0.0.1`    | The public IP address or domain name for accessing SCC.                                                                                                                                         |
| `SCC_PORT`          | `80`           | The port on which the Flask app runs. Ensure this matches the Docker Compose configuration.                                                                                                     |
| `SCC_PLAYLIST_PORT` | **Required**   | The port used for playlist proxying.                                                                                                                                                            |
| `FLASK_HOST`        | `0.0.0.0`      | Host address for the Flask app. Change if needed.                                                                                                                                               |
| `FLASK_DEBUG`       | `true`         | Enables debug mode for detailed logs.                                                                                                                                                           |
| `PLAYLIST_NAME`     | `playlist.m3u` | The name of the generated playlist file. Change if necessary but retain the `.m3u` extension.                                                                                                   |
| `CHANNEL_TAG`       | `tvg-name`     | The name of the channel TAG inside your m3u playlist.                                                                                                                                           |

<br />

## How SCC Works

1. **Launch the application**: Run `docker-compose up -d` to start SCC.
2. **Configure playlist.json**: SCC initializes a `playlist.json` file in the `scc` directory. This file lists channels and their associated stream IDs.
3. **Monitor changes**: SCC continuously watches `playlist.json` for updates. If changes are detected, SCC regenerates the M3U playlist file (`playlist.m3u` or the name specified in `PLAYLIST_NAME`).
4. **Access the playlist**: The generated playlist file is available at:
   ```
   <WEB_PROTOCOL>://<WEB_HOSTNAME>/<PLAYLIST_NAME>
   ```
   For example, `http://127.0.0.1/playlist.m3u`.

<br />

## Contributing

We welcome contributions to improve SCC! To contribute:

1. Fork the repository.
2. Create a feature branch.
3. Commit your changes.
4. Open a pull request for review.

<br />

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](https://choosealicense.com/licenses/gpl-3.0/) file for details.