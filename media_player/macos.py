"""
Provide functionality to interact with afplay on macOS.
For more details about this platform, please refer to the documentation at
https://github.com/rotx/homeassistant-components/
"""
import os
import shutil
import subprocess
import logging
import voluptuous as vol
import urllib.request

from homeassistant.components.media_player import (
    SUPPORT_PLAY_MEDIA, MediaPlayerDevice, MEDIA_TYPE_MUSIC)
from homeassistant.const import (CONF_NAME, STATE_IDLE, STATE_PLAYING)

_LOGGER = logging.getLogger(__name__)

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the macos platform."""
    if shutil.which("afplay", path="/usr/bin") is None:
        _LOGGER.error("'/usr/bin/afplay' was not found")
        return
    if shutil.which("reattach-to-user-namespace", path="/usr/local/bin") is None:
        _LOGGER.error("'/usr/local/bin/reattach-to-user-namespace' was not found")
        return
    add_devices([MacOSDevice()])

class MacOSDevice(MediaPlayerDevice):
    """Representation of a macos player."""

    def __init__(self):
        """Initialize the macos device."""
        self._name = 'macos'
        self._state = STATE_IDLE
        
    def update(self):
        """Get the latest details from the device."""
        return True

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
        
        local_filename, msg = urllib.request.urlretrieve(media_id)

        self._state = STATE_PLAYING
        subprocess.call(['/usr/local/bin/reattach-to-user-namespace', '/usr/bin/afplay', local_filename])
        self._state = STATE_IDLE

        os.unlink(local_filename)


