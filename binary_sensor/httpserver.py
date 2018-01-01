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

CONF_LISTEN_PORT = 'listen_port'
CONF_PATH = 'set_path'
CONF_RESET = 'reset_delay'

DEFAULT_LISTEN_PORT = 8130
DEFAULT_RESET = 20

SENSOR_SCHEMA = vol.Schema({
    vol.Optional(ATTR_FRIENDLY_NAME): cv.string,
    vol.Required(CONF_PATH): cv.string,
    vol.Optional(CONF_DEVICE_CLASS): DEVICE_CLASSES_SCHEMA,
    vol.Optional(CONF_RESET, default=DEFAULT_RESET): cv.positive_int
})

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_LISTEN_PORT, default=DEFAULT_LISTEN_PORT): cv.port,
    vol.Required(CONF_SENSORS): vol.Schema({cv.slug: SENSOR_SCHEMA})
})


# pylint: disable=unused-argument
@asyncio.coroutine
def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    """Set up the httpserver binary sensor platform."""
    sensors = []
    request_paths = dict()

    listen_port = config.get(CONF_LISTEN_PORT)

    try:
        httpserver = HTTPThread(hass, request_paths, listen_port)
    except (OSError, PermissionError) as ex:
        _LOGGER.error("Exception %s: Cannot start HTTP server", str(ex))
        return False

    for device, device_config in config[CONF_SENSORS].items():
        friendly_name = device_config.get(ATTR_FRIENDLY_NAME, device)
        device_class = device_config.get(CONF_DEVICE_CLASS)
        path = device_config.get(CONF_PATH)
        reset = device_config.get(CONF_RESET)

        this_sensor = HttpServerBinarySensor(hass, device, friendly_name,
                                             device_class, path, reset)
        request_paths[path] = this_sensor
        sensors.append(this_sensor)

    if not sensors:
        _LOGGER.error("No sensors added")
        return False

    async_add_devices(sensors)

    httpserver.start()

    return True


class RequestHandler(BaseHTTPRequestHandler):
    """Basic HTTP server with GET only, and without logging."""
    # pylint: disable=C0103
    def do_GET(self):
        """Override the GET method to trigger a binary sensor."""
        bsensor = self.server.request_paths.get(self.path)
        if bsensor is None:
            self.send_error(404)
        else:
            self.send_response(200)
            _LOGGER.debug("Setting %s", bsensor.entity_id)
            bsensor.set_state(True)
        self.end_headers()

    # pylint: disable=W0622
    def log_message(self, format, *args):
        """Don't log to stderr."""
        _LOGGER.debug("%s - - [%s] %s",
                      self.address_string(),
                      self.log_date_time_string(),
                      (format%args))


class HTTPThread(threading.Thread):
    """Background thread for HTTP server."""

    def __init__(self, hass, request_paths, port=DEFAULT_LISTEN_PORT):
        """Initialize HTTP server thread."""
        super(HTTPThread, self).__init__()

        self.daemon = True
        self.hass = hass
        self.server = HTTPServer(('', port), RequestHandler)
        self.server.request_paths = request_paths


    def run(self):
        """Handle incoming HTTP requests."""
        try:
            self.server.serve_forever()
        except Exception as ex:
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
                 path, reset):
        """Initialize the httpserver sensor."""
        self.hass = hass
        self.entity_id = async_generate_entity_id(
            ENTITY_ID_FORMAT, device, hass=hass)
        self._name = friendly_name
        self._device_class = device_class
        self._state = False
        self._path = path
        self._reset_delay = reset
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
        """Return the name of the httpserver sensor."""
        return self._name

    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
        return self._state

    def set_state(self, state):
        """Set state of binary sensor."""
        self._state = state
        self.async_schedule_update_ha_state()

        def _delayed_reset():
            """Timer callback for sensor update."""
            _LOGGER.debug("%s Resetting state (%ssec)",
                          self._name, self._reset_delay)
            self._state = False
            self.async_schedule_update_ha_state()

        # Set timer to clear state
        if self._timer is not None and self._timer.isAlive():
            self._timer.cancel()

        self._timer = threading.Timer(self._reset_delay, _delayed_reset)
        self._timer.start()

