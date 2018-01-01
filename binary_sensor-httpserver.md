# binary_sensor.httpserver

This component starts a local http web server and waits for connections. When a client connects with a GET request,
the URL is parsed and a binary sensor is triggered.

Three types of sensors are supported:
| Type | Configuration | Description |
| --- | --- | --- |
| self-resetting | `set_path`, `reset_delay` | Triggered by GET to set_path, resets to off after reset_delay seconds |
| toggle | `set_path` | GET to set_path toggles state |
| set-reset | `set_path`, `reset_path` | GET to set_path turns on, GET to reset_path turns off |

## Component Installation
Copy `binary_sensor/httpserver.py` to `custom_components/binary_sensor/httpserver.py`.

## Component Configuration
In `configuration.yaml`, add the new `httpserver` binary_sensor platform.
Under `sensors`, add one _sensor_ for each HTTP URL path you wish to respond to. Each of these will create one
binary sensor in Home Assistant.

The `listen_port` is an available local port.

### Per-Sensor Configuration

| Key | Description |
| --- | --- |
| `set_path` | URL path to turn sensor on, or to toggle. |
| `reset_path` | URL path to turn sensor off (set-reset only). |
| `friendy_name` | User facing name for the sensor. |
| `device_class` | A supported binary_sensor device class. See [documentation](https://home-assistant.io/components/binary_sensor/). |
| `reset_delay` | For self-resetting sensors, the time in seconds after triggering when the sensor returns to _False_ (off). |
| `initial_state` | _True_ or _False_. Sensor state on startup, defaults to _False_ (off) |


### Examples
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

## Component Test
Use `curl` to trigger the binary sensor. If the Home Assistant server IP is 10.11.12.100, then the test command for the
self-resetting sensor shown in the example would be:
```
$ curl http://10.11.12.100:8130/motion/garage
```
Since Home Assistant will return a "200" (OK) HTTP status, curl will not print anything on success. curl will return an
error message however in case of invalid IP:port or a non-configured path.


## Example: Foscam FI8910W Motion Sensor

Foscam FI8910W can post http requests when it detects motion.
***Note: This feature is not available on newer cameras.***

The following describes cameras following the API in [IP Camera CGI V1.27](https://www.foscam.es/descarga/ipcam_cgi_sdk.pdf).

The camera does not post another request when the sensor clears, so we need to configure a _self-resetting sensor_.

To get the current settings of your Foscam (in the example, the camera is at address 10.11.12.13 port 80):
```
$ curl "http://10.11.12.13:80/get_params.cgi?user=USER&pwd=PASSWORD"

...
var alarm_motion_armed=0;
var alarm_http=0;
var alarm_http_url=;
...

```

Pick a free local port number on the Home Assistant system. In this example, we're using port 8130 which is not otherwise used. HA is at IP 10.11.12.100.

## Configure and Test the Foscam

Enable the motion sensor (which could also be done using the camera's web UI), and
set the parameters http and http_url (these are hidden in the camera's web UI) using `curl`:
```
$ curl "http://10.11.12.13:80/set_alarm.cgi?user=USER&pwd=PASSWORD&motion_armed=1&http=1&http_url=http://10.11.12.100:8130/motion/garage"
ok.
```

Other options such as sensitivity and motion compensation can be set in the web UI.

You can test whether the motion alarms are working without setting up a httpserver binary_sensor.
To do so, start a local http server on the PORT you specified in the camera's http_url.
This is easiest using `nc`:
```
$ nc -l 8130
```

Then, get the camera to trigger and you should see:
```
GET /motion/garage HTTP/1.0
HOST: 10.11.12.100:8130
User-Agent: myclient/1.0 me@null.net
```

