#!/usr/bin/env python3
"""Launch SSR with an ISO 8601 filename and the existing recording settings."""
import configparser
from datetime import datetime
from pathlib import Path
import subprocess
import tempfile


def main():
    settings = Path.home() / '.ssr/settings.conf'
    config = configparser.ConfigParser(interpolation=None, strict=False)
    config.optionxform = str
    config.read(settings)
    if not config.has_section('output'):
        config.add_section('output')
    previous = Path(config.get('output', 'file', fallback=str(
        Path.home() / 'Videos/SimpleScreenRecorder/recording.mkv')))
    previous.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().astimezone().isoformat(timespec='microseconds')
    config.set('output', 'file', str(previous.parent / (stamp + (previous.suffix or '.mkv'))))
    config.set('output', 'add_timestamp', 'false')
    # A separate settings file avoids overwriting a running recorder's settings.
    with tempfile.TemporaryDirectory(prefix='screen-recorder-') as temp:
        session = Path(temp) / 'settings.conf'
        with session.open('w') as stream:
            config.write(stream, space_around_delimiters=False)
        return subprocess.call(['simplescreenrecorder', '--settingsfile=' + str(session)])


if __name__ == '__main__':
    raise SystemExit(main())
