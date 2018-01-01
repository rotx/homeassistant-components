"""
Support for binary sensors triggered by http GET requests.

For more details about this component, please refer to the documentation at
https://github.com/rotx/homeassistant-components/
"""

import asyncio
import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import voluptuous as vol

from homeassistant.components.binary_sensor import (
    BinarySensorDevice, ENTITY_ID_FORMAT, PLATFORM_SCHEMA,
    DEVICE_CLASSES_SCHEMA)
from homeassistant.const import (
    ATTR_FRIENDLY_NAME, CONF_SENSORS, CONF_DEVICE_CLASS)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import async_generate_entity_id


_LOGGER = logging.getLogger(__name__)

CONF_INITIAL_STATE = 'initial_state'
CONF_LISTEN_PORT = 'listen_port'
CONF_RESET_DELAY = 'reset_delay'
CONF_RESET_PATH = 'reset_path'
CONF_SET_PATH = 'set_path'

DEFAULT_INITIAL_STATE = False
DEFAULT_LISTEN_PORT = 8130

SENSOR_SCHEMA = vol.Schema({
    vol.Optional(ATTR_FRIENDLY_NAME): cv.string,
    vol.Optional(CONF_DEVICE_CLASS): DEVICE_CLASSES_SCHEMA,
    vol.Optional(CONF_INITIAL_STATE, default=DEFAULT_INITIAL_STATE):
        cv.boolean,
    vol.Optional(CONF_RESET_DELAY, default=0): cv.positive_int,
    vol.Optional(CONF_RESET_PATH): cv.string,
    vol.Required(CONF_SET_PATH): cv.string
})

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_LISTEN_PORT, default=DEFAULT_LISTEN_PORT): cv.port,
    vol.Required(CONF_SENSORS): vol.Schema({cv.slug: SENSOR_SCHEMA})
})


@asyncio.coroutine
def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    """Set up the httpserver binary sensor platform."""
    sensors = []
    request_paths = dict()

    listen_port = config.get(CONF_LISTEN_PORT)

    try:
        httpserver = HTTPThread(request_paths, listen_port)
    except (OSError, PermissionError) as ex:
        _LOGGER.error("Exception %s: Cannot start HTTP server", str(ex))
        return False

    for device, device_config in config[CONF_SENSORS].items():
        device_class = device_config.get(CONF_DEVICE_CLASS)
        friendly_name = device_config.get(ATTR_FRIENDLY_NAME, device)
        initial_state = device_config.get(CONF_INITIAL_STATE)
        reset_delay = device_config.get(CONF_RESET_DELAY)
        set_path = device_config.get(CONF_SET_PATH)
        reset_path = device_config.get(CONF_RESET_PATH)

        if set_path == reset_path:
            _LOGGER.error("set_path and reset_path %s cannot be the same",
                          set_path)
            return False

        is_toggle = (reset_path is None and reset_delay == 0)

        this_sensor = HttpServerBinarySensor(hass, device, friendly_name,
                                             device_class, reset_delay,
                                             initial_state, is_toggle)
        request_paths[set_path] = this_sensor.set_state
        if reset_path is not None:
            request_paths[reset_path] = this_sensor.reset_state
        sensors.append(this_sensor)

    if not sensors:
        _LOGGER.error("No sensors added")
        return False

    async_add_devices(sensors)

    httpserver.start()

    return True


class RequestHandler(BaseHTTPRequestHandler):
    """Basic HTTP server with GET only, and without logging."""

    # pylint: disable=invalid-name
    def do_GET(self):
        """Override the GET method to trigger a binary sensor."""
        action = self.server.request_paths.get(self.path)
        if action is None:
            self.send_error(404)
        else:
            self.send_response(200)
            _LOGGER.debug("Action for %s", self.path)
            action()
        self.end_headers()

    # pylint: disable=redefined-builtin
    def log_message(self, format, *args):
        """Log HTTP access to HA log (don't log to stderr)."""
        _LOGGER.info("%s - - [%s] %s",
                     self.address_string(),
                     self.log_date_time_string(),
                     (format % args))


class HTTPThread(threading.Thread):
    """Background thread for HTTP server."""

    def __init__(self, request_paths, port=DEFAULT_LISTEN_PORT):
        """Initialize HTTP server thread."""
        super(HTTPThread, self).__init__()

        self.daemon = True
        self.server = HTTPServer(('', port), RequestHandler)
        self.server.request_paths = request_paths

    def run(self):
        """Handle incoming HTTP requests."""
        try:
            self.server.serve_forever()
        except IOError as ex:
            _LOGGER.error("Exception %s: Closing HTTP server", str(ex))
        finally:
            self.server.server_close()

    def terminate(self):
        """Stop and join thread."""
        self.server.shutdown()
        self.join()


class HttpServerBinarySensor(BinarySensorDevice):
    """representation of a httpserver binary sensor."""

    def __init__(self, hass, device, friendly_name, device_class,
                 reset_delay, initial_state, is_toggle):
        """Initialize the httpserver sensor."""
        self.hass = hass
        self.entity_id = async_generate_entity_id(
            ENTITY_ID_FORMAT, device, hass=hass)
        self._name = friendly_name
        self._device_class = device_class
        self._reset_delay = reset_delay
        self._state = initial_state
        self._is_toggle = is_toggle
        self._timer = None

    @property
    def device_class(self):
        """Return the class of this sensor."""
        return self._device_class

    @property
    def should_poll(self):
        """No polling needed for a httpserver binary sensor."""
        return False

    @property
    def name(self):
        """Return the name of the httpserver binary sensor."""
        return self._name

    @property
    def is_on(self):
        """Return true if the httpserver binary sensor is on."""
        return self._state

    def reset_state(self):
        """Reset the state of the httpserver binary sensor."""
        self._state = False
        self.async_schedule_update_ha_state()

    def set_state(self):
        """Toggle or set the state of the httpserver binary sensor."""
        if self._is_toggle:
            self._state = not self._state
        else:
            self._state = True
        self.async_schedule_update_ha_state()

        # Set timer to auto-clear state
        if self._reset_delay != 0:
            if self._timer is not None and self._timer.isAlive():
                self._timer.cancel()

            self._timer = threading.Timer(self._reset_delay, self.reset_state)
            self._timer.start()
