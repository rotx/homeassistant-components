# Additional Components for Home Assistant

## tts.macos

This component uses the locally installed, high quality text-to-speech engine in macOS. See [tts.macos](tts-macos.md).

## media_player.macos

This component uses the locally installed `afplay` macOS utility to play media files on the selected sound output source.
See [media_player.macos](media_player-macos.md).

## binary_sensor.httpserver

This component starts a local http web server and waits for connections. When a client connects with a GET request, the URL
is parsed and a binary sensor is triggered. See [binary_sensor.httpserver](binary_sensor-httpserver.md).
