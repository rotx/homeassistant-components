# media_player.macos

This component uses the locally installed `afplay` macOS utility to play media files on the selected sound output source.
This is especially useful for tts. `afplay` supports only a single function, `play_media` with type `MUSIC`.

## Component Installation

Copy `media_player/macos.tty` to `custom_components/media_player/macos.py`.

Enable in `configuration.yaml`:

```
media_player:
  - platform: macos
```

## Component Test

See the macos tts component and repeat the `tts` test. If the Mac's default speaker is on, you should hear the synthesized voice.
