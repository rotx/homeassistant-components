"""
Support for the macOS speech service.

For more details about this component, please refer to the documentation at
https://github.com/rotx/homeassistant-components
"""
import os
import tempfile
import shutil
import subprocess
import asyncio
import logging

import voluptuous as vol

from homeassistant.components.tts import Provider, PLATFORM_SCHEMA, CONF_LANG

_LOGGER = logging.getLogger(__name__)

CONF_VOICE = 'voice'

# Get installed voices and languages
_SAY_OUTPUT = subprocess.check_output(
    ['/usr/local/bin/reattach-to-user-namespace',
     '/usr/bin/say', '-v', '?']).splitlines()
SUPPORT_LANGUAGES = list(set([v.split()[1].decode().replace('_', '-')
                              for v in _SAY_OUTPUT]))
SUPPORT_VOICES = [v.split()[0].decode() for v in _SAY_OUTPUT]

DEFAULT_LANG = 'en-US'
DEFAULT_VOICE = 'Alex'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_LANG, default=DEFAULT_LANG): vol.In(SUPPORT_LANGUAGES),
    vol.Optional(CONF_VOICE, default=DEFAULT_VOICE): vol.In(SUPPORT_VOICES)
})


@asyncio.coroutine
def async_get_engine(hass, config):
    """Set up macOS speech component."""
    if shutil.which('say', path='/usr/bin') is None:
        _LOGGER.error("'/usr/bin/say' not found")
        return False
    if shutil.which('reattach-to-user-namespace',
                    path='/usr/local/bin') is None:
        _LOGGER.error("'/usr/local/bin/reattach-to-user-namespace' not found")
        return False
    return MacOSProvider(config[CONF_LANG], config[CONF_VOICE])


class MacOSProvider(Provider):
    """The macOS TTS provider."""

    def __init__(self, lang, voice):
        """Initialize macOS TTS provider."""
        self.name = 'macos'
        # m4a works. wave, aiff, mp3, mp4 do not.
        self._codec = 'm4a'
        self._lang = lang
        self._voice = voice

    @property
    def default_language(self):
        """Return the default language."""
        return self._lang

    @property
    def supported_languages(self):
        """Return list of supported languages."""
        return SUPPORT_LANGUAGES

    @property
    def default_voice(self):
        """Return the default voice."""
        return self._voice

    @property
    def supported_voices(self):
        """Return list of supported voices."""
        return SUPPORT_VOICES

    @property
    def supported_options(self):
        """Return list of supported options."""
        return [CONF_VOICE]

    @asyncio.coroutine
    def async_get_tts_audio(self, message, language, options=None):
        """Load TTS using say."""
        with tempfile.NamedTemporaryFile(suffix='.'+self._codec,
                                         delete=False) as tmpf:
            fname = tmpf.name

        # See https://github.com/ChrisJohnsen/tmux-MacOSX-pasteboard
        subprocess.call(['/usr/local/bin/reattach-to-user-namespace',
                         '/usr/bin/say', '-v', self._voice,
                         '-o', fname, message])

        data = None
        try:
            with open(fname, 'rb') as voice:
                data = voice.read()
        except OSError:
            _LOGGER.error("Error trying to read %s", fname)
        finally:
            os.remove(fname)

        if data:
            return (self._codec, data)
        return (None, None)
