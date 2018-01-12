import yaml
import pathlib

_secrets_path = pathlib.Path('secrets.yml')
_override_path = pathlib.Path('secrets.override.yml')

# get secrets
with _secrets_path.open() as f:
    _SECRETS = yaml.load(f)

# override secrets if possible
# this override file should not be checked into version control!
if _override_path.is_file():
    with _override_path.open() as f:
        _SECRETS.update(yaml.load(f))


SPOTIFY_CLIENT_ID = _SECRETS['spotify']['CLIENT_ID']
SPOTIFY_CLIENT_SECRET = _SECRETS['spotify']['CLIENT_SECRET']
