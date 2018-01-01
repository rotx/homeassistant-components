# tts.macos

This component uses the locally installed, high quality text-to-speech engine in macOS.

## Prerequisites

As of Mac OS X 10.6, macOS requires that the speech synthesizer is invoked inside a user name space - otherwise, the `say` process will just hang forever because the system cannot create a `speechsynthesizerd` process.

Since Home Assistant itself will run as a daemon (detached from the user),
the macos tts component requires the installation of a helper program. The easiest way to do this is to install using
homebrew (brew.sh):
```
brew install reattach-to-user-namespace
```

This installs a small executable into `/usr/local/bin`, aptly named `reattach-to-user-namespace`. See https://github.com/ChrisJohnsen/tmux-MacOSX-pasteboard for technical details.

## Component Installation

Copy `tts/macos.py` to `custom_components/tts/macos.py`.

Enable and configure in `configuration.yaml`:

``` 
tts:
  - platform: macos
    voice: 'Ava'
```

Available voices are listed in System Preferences (Accessibility > Speech as of High Sierra), or you can use the `say` command:
```
$ say -v'?'
Amelie              fr_CA    # Bonjour, je m’appelle Amelie. Je suis une voix canadienne.
Ava                 en_US    # Hello, my name is Ava. I am an American-English voice.
Daniel              en_GB    # Hello, my name is Daniel. I am a British-English voice.
Diego               es_AR    # Hola, me llamo Diego y soy una voz española.
...
```
**Make sure you download at least one high-quality voice** using System Preferences (possibly listed as "enhanced" or "premium").
Alex, Ava, and Samantha are good choices.

_Note: While it's possible to configure a language such as en-US, the language setting is ignored. Select a matching voice
instead._

## Component Test

Use the developer tools in the web interface to call the service `tts.macos_say` with service data
`{"message": "Hello world, can you hear me now?"}`.

If you have not yet configured a media player, Home Assistant will add a log entry
```
2017-12-29 23:55:02 WARNING (MainThread) [homeassistant.core] Unable to find service media_player/play_media
```

In any case, the sythesized speech can be found in the cache directory `tts`, for example:
```
-rw-r--r--  1 _ha _ha 44552 Dec 29 23:55 cafebabedeadbeef0badabbababafeca_en-us_-_macos.m4a
```

The macos tts component saves synthesized speech in `m4a` (MPEG-4 Audio) format. Not only does this save disk space, but it's one
of the few formats both Home Assistant's tts and macOS understand.

You can play these files using `afplay` (see the macos media_server component).
