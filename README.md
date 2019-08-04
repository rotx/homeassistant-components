# Components for Home Assistant

## macOS Text-to-Speech and Media Player

This component uses the locally installed, high quality text-to-speech (TTS) engine in macOS and
the locally installed `afplay` macOS utility to play media files on the selected sound output
source.

### Prerequisites

As of Mac OS X 10.6, macOS requires that the speech synthesizer is invoked inside a user name
space - otherwise, the `say` process will just hang forever because the system cannot create a
`speechsynthesizerd` process.

Since Home Assistant itself will run as a daemon (detached from the user), the macOS TTS component
requires the installation of a helper program. The easiest way to do this is to install using
HomeBrew (https://brew.sh):
```
brew install reattach-to-user-namespace
```

This installs a small executable into `/usr/local/bin`, aptly named `reattach-to-user-namespace`.
See https://github.com/ChrisJohnsen/tmux-MacOSX-pasteboard for technical details.

### Component Installation

Copy `custom_components/macos_tts` to `custom_components/macos_tts` inside your Home Assistant
configuration folder.

Enable and configure in `configuration.yaml`:

``` 
tts:
  - platform: macos_tts
    voice: 'Ava'

media_player:
  - platform: macos_tts
```

Available voices are listed in System Preferences (Accessibility > Speech as of High Sierra), or
you can use the `say` command:
```
$ say -v'?'
Amelie              fr_CA    # Bonjour, je m’appelle Amelie. Je suis une voix canadienne.
Ava                 en_US    # Hello, my name is Ava. I am an American-English voice.
Daniel              en_GB    # Hello, my name is Daniel. I am a British-English voice.
Diego               es_AR    # Hola, me llamo Diego y soy una voz española.
...
```
**Make sure you download at least one high-quality voice** using System Preferences (possibly
listed as "enhanced" or "premium").
Alex, Ava, and Samantha are good choices.

_Note: While it's possible to configure a language such as en-US, the language setting is ignored.
Select a matching voice instead._

### Component Test

Use the developer tools - services in the web interface to call the service `tts.macos_tts_say`
with service data
```
{"message": "Hello world, can you hear me now?"}
```

If the Mac's default speaker is on and the media player component is working, you should hear the
synthesized voice. If you have not yet configured a media player, and the log level is set to
allow it, Home Assistant will add a log entry
```
2017-12-29 23:55:02 WARNING (MainThread) [homeassistant.core] Unable to find service ...
```

In any case, the synthesized speech can be found in the cache directory `tts`, for example:
```
-rw-r--r--  1 _ha _ha 44552 Dec 29 23:55 cafebabedeadbeef0badabbababafeca_en-us_-_macos_tts.m4a
```

The macOS TTS component saves synthesized speech in `m4a` (MPEG-4 Audio) format. Not only does this
save disk space, but it's one of the few formats both Home Assistant's TTS and macOS understand.

You can play these files using `afplay`.

-----

## binary_sensor.httpserver

This component starts a local http web server and waits for connections. When a client connects
with a GET request, the URL is parsed and a binary sensor is triggered.

Three types of sensors are supported:
| Type | Configuration | Description |
| --- | --- | --- |
| self-resetting | `set_path`, `reset_delay` | Triggered by GET to set_path, resets to off after reset_delay seconds |
| toggle | `set_path` | GET to set_path toggles state |
| set-reset | `set_path`, `reset_path` | GET to set_path turns on, GET to reset_path turns off |

### Component Installation
Copy `custom_components/httpserver` to `custom_components/httpserver` in your Home Assistant
configuration folder.

### Component Configuration
In `configuration.yaml`, add the new `httpserver` binary_sensor platform.
Under `sensors`, add one _sensor_ for each HTTP URL path you wish to respond to. Each of these will
create one binary sensor in Home Assistant.

The `listen_port` is an available local port.

#### Per-Sensor Configuration

| Key | Description |
| --- | --- |
| `set_path` | URL path to turn sensor on, or to toggle. |
| `reset_path` | URL path to turn sensor off (set-reset only). |
| `friendy_name` | User facing name for the sensor. |
| `device_class` | A supported binary_sensor device class. See [documentation](https://home-assistant.io/components/binary_sensor/). |
| `reset_delay` | For self-resetting sensors, the time in seconds after triggering when the sensor returns to _False_ (off). |
| `initial_state` | _True_ or _False_. Sensor state on startup, defaults to _False_ (off) |


#### Examples
```
binary_sensor:
  - platform: httpserver
    listen_port: 8130
    sensors:
      foscam_motion:
        set_path: "/motion/garage"
        friendly_name: "Garage Motion (self-resetting)"
        device_class: motion
        reset_delay: 20
      toggle_sensor:
        set_path: "/sensor/toggle"
        friendly_name: "Toggle Sensor"
        device_class: motion
        initial_state: True
      set_reset_sensor:
        set_path: "/sensor/set/1"
        reset_path: "/sensor/set/0"
        friendly_name: "Set-Reset Sensor"
        device_class: motion
```

Restart Home Assistant.

### Component Test
Use `curl` to trigger the binary sensor. If the Home Assistant server IP is 10.11.12.100, then the
test command for the self-resetting sensor shown in the example would be:
```
$ curl http://10.11.12.100:8130/motion/garage
```
Since Home Assistant will return a "200" (OK) HTTP status, curl will not print anything on success.
curl will return an error message however in case of invalid IP:port or a non-configured path.


## Example: Foscam FI8910W Motion Sensor

Foscam FI8910W can post http requests when it detects motion.
***Note: This feature is not available on newer cameras.***

The following describes cameras following the API in
[IP Camera CGI V1.27](https://www.foscam.es/descarga/ipcam_cgi_sdk.pdf).

The camera does not post another request when the sensor clears, so we need to configure a
_self-resetting sensor_.

To get the current settings of your Foscam (in the example, the camera is at address
10.11.12.13 port 80):
```
$ curl "http://10.11.12.13:80/get_params.cgi?user=USER&pwd=PASSWORD"

...
var alarm_motion_armed=0;
var alarm_http=0;
var alarm_http_url=;
...
```

Pick a free local port number on the Home Assistant system. In this example, we're using port 8130
which is not otherwise used. HA is at IP 10.11.12.100.

### Configure and Test the Foscam

Enable the motion sensor (which could also be done using the camera's web UI), and set the
parameters http and http_url (these are hidden in the camera's web UI) using `curl`:
```
$ curl "http://10.11.12.13:80/set_alarm.cgi?user=USER&pwd=PASSWORD&motion_armed=1&http=1&http_url=http://10.11.12.100:8130/motion/garage"
ok.
```

Other options such as sensitivity and motion compensation can be set in the web UI.

You can test whether the motion alarms are working without setting up a httpserver binary_sensor.
To do so, start a local http server on the PORT you specified in the camera's http_url. This is
easiest using `nc`:
```
$ nc -l 8130
```

Then, get the camera to trigger and you should see:
```
GET /motion/garage HTTP/1.0
HOST: 10.11.12.100:8130
User-Agent: myclient/1.0 me@null.net
```