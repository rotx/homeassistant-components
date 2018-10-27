"""
Provide functionality to interact with afplay on macOS.

For more details about this platform, please refer to the documentation at
https://github.com/rotx/homeassistant-components/
"""
import logging
import os
import shutil
import subprocess
import urllib.request

import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.components.media_player import (MEDIA_TYPE_MUSIC,
                                                   PLATFORM_SCHEMA,
                                                   SUPPORT_PLAY_MEDIA,
                                                   MediaPlayerDevice)
from homeassistant.const import CONF_NAME, STATE_IDLE, STATE_PLAYING

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = 'macos'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the macos platform."""
    if shutil.which('afplay', path='/usr/bin') is None:
        _LOGGER.error("'/usr/bin/afplay' not found")
        return
    name = config.get(CONF_NAME)
    add_devices([MacOSDevice(name)])


class MacOSDevice(MediaPlayerDevice):
    """Representation of a macos player."""

    def __init__(self, name):
        """Initialize the macos device."""
        self._name = name
        self._state = STATE_IDLE

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def supported_features(self):
        """Flag media player features that are supported."""
        return SUPPORT_PLAY_MEDIA

    @property
    def media_content_type(self):
        """Content type of current playing media."""
        return MEDIA_TYPE_MUSIC

    def play_media(self, media_type, media_id, **kwargs):
        """Play media from a URL or file."""
        if not media_type == MEDIA_TYPE_MUSIC:
            _LOGGER.error(
                "Invalid media type %s. Only %s is supported",
                media_type, MEDIA_TYPE_MUSIC)
            return

        try:
            fname = urllib.request.urlretrieve(media_id)[0]

            self._state = STATE_PLAYING
            subprocess.call(['/usr/bin/afplay', fname])
            self._state = STATE_IDLE

        except OSError:
            _LOGGER.error("Error trying to request and play %s", media_id)

        finally:
            urllib.request.urlcleanup()
