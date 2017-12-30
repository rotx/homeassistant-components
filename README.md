# Additional Components for Home Assistant

## tts/macos

This component uses the locally installed, high quality text-to-speech engine in macOS.

### OS Preparation

As of Mac OS X 10.6, macOS requires that the speech synthesizer is invoked inside a user name space - otherwise, the `say` process will just hang forever because the system cannot create a `speechsynthesizerd` process.

Since Home Assistant itself will run as a daemon (detached from the user),
this component requires the installation of a help program from homebrew (brew.sh):
```
brew install reattach-to-user-namespace
```

The installs a small executable into `/usr/local/bin`, aptly named `reattach-to-user-namespace`.

### Component Installation

Copy `tts/macos.py` to `custom_components/tts/macos.py`.

Enable and configure in `configuration.yaml`:

``` 
tts:
  - platform: macos
    voice: 'Ava'
```

Available voices are listed in System Preferences (Accessibility > Speech as of High Sierra).
Make sure you download at least one high-quality voice first. Alex, Ava, and Samantha are good choices.

### Component Test

Use the developer tools in the web interface to call the service `tts.macos_say` with service data `{"message": "Hello world, can you hear me now?"}`.

If you have not yet configured a media player, Home Assistant will add a log entry
```
2017-12-29 23:55:02 WARNING (MainThread) [homeassistant.core] Unable to find service media_player/play_media
```

In any case, the sythesized speech can be found in the cache directory `tts`, for example:
```
-rw-r--r--  1 _ha _ha 44552 Dec 29 23:55 3f19336891bcaabfb5_en_us_-_macos.m4a
```

You can play this file using `afplay`.