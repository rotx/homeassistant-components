# binary_sensor.httpserver

This component starts a local http web server and waits for connections. When a client connects with a GET request,
the URL is parsed and a binary sensor is triggered.

For example, Foscam FI8910W can post http requests when it detects motion.
***Note: This feature is not available on newer cameras.***

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

Next, test whether the motion alarms are working. To do so, start a local http server
on the PORT you specified. This is easiest using `nc`:
```
$ nc -l 8130
```

Then, get the camera to trigger and you should see:
```
GET /motion/garage HTTP/1.0
HOST: 10.11.12.100:8130
User-Agent: myclient/1.0 me@null.net
```

## Component Installation
Copy `binary_sensor/httpserver.py` to `custom_components/binary_sensor/httpserver.py`.

## Component Configuration
In `configuration.yaml`, add the new _httpserver_ binary_sensor platform. Add one _sensor_ for each HTTP
path you wish to respond to. Home Assistant will create one binary sensor for each.
The `listen_port` is an available local port (the _PORT_ mentioned above).
`reset_delay` is the time in seconds after triggering when the sensor returns to its "off" state.
`device_class` is a standard binary_sensor device class.

```
binary_sensor:
  - platform: httpserver
    listen_port: 8130
    sensors:
      foscam_motion:
        friendly_name: "Garage Motion"
        device_class: motion
        set_path: "/motion/garage"
        reset_delay: 20
```

Restart Home Assistant.

## Component Test
Use `curl` to trigger the binary sensor.
```
$ curl http://10.11.12.100:8130/motion/garage
```
Since Home Assistant will return a "200" (OK) HTTP status, curl will not print anything. curl will return an
error message however in case of invalid IP:port or a non-configured path.

Next, trigger motion and the camera should cause the sensor to trip and then reset after the specified time.
