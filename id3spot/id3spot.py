from spotipy.oauth2 import SpotifyClientCredentials
from eyed3.id3.frames import ImageFrame
from eyed3.id3.tag import TagTemplate
from eyed3.utils.console import printError, printWarning, AnsiCodes
from eyed3.plugins.classic import ARGS_HELP
from eyed3.utils.log import log
import config
import logging
import pathlib
import spotipy
import requests
import eyed3
import click
import re
import utils


client_credentials_manager = SpotifyClientCredentials(
    client_id=config.SPOTIFY_CLIENT_ID,
    client_secret=config.SPOTIFY_CLIENT_SECRET
)

sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

AnsiCodes.init(True)

@click.command()
@click.option('--query', '-q',  help='Specify a query to use when searching for a matching track.')
@click.option('--replace', '-r', help='Replace original tags entirely', flag_value=True)
@click.option('--rename', '-R', help=ARGS_HELP['--rename'])
@click.option('--analyze', '-a', help='Include ID3 tags for bpm and key from Spotify.', flag_value=True)
@click.option('--dry-run', '-d', help='Perform lookup but do not write tags.', flag_value=True)
@click.option('--magic', '-x', help='Shortcut for id3spot.py -arpR "$artist - $title"', flag_value=True)
@click.option('--prompt', '-p', help='If song is not exact match, prompt before using information.', flag_value=True)
@click.option('--verbose', '-v', help='Output diff for each file processed.', flag_value=True)
@click.argument('files', nargs=-1, type=click.Path(exists=True, dir_okay=False, readable=True, writable=True))
def main(files, **kwargs):
    if kwargs['magic']:
        kwargs.update(replace=True, rename='$artist - $title', analyze=True, prompt=True)
    if kwargs['dry_run']:
        kwargs.update(verbose=True)
    if not kwargs['verbose']:
        log.setLevel(logging.ERROR)

    for file in files:
        process(file, **kwargs)


def search_spotify(term):
    try:
        track = sp.search(term, type='track', limit=1)['tracks']['items'][0]
    except:
        track = None

    if not track:
        return None

    album = sp.album(track['album']['id'])

    # get total discs, going through spotify paging object if necessary
    last_tracks = album['tracks']
    while last_tracks['next']:
        last_tracks = sp.next(last_tracks)

    total_discs = last_tracks['items'][-1]['disc_number']

    # spotify likes to use dashes instead of parentheses for remixes
    title = re.sub('\s-\s([\w\.\?]+?\sremix)$', ' (\g<1>)', track['name'], flags=re.I)

    # returning tuple of dicts (tag_data, meta)
    return {
        'title': title,
        # 'track_num': (track['track_number'], album['tracks']['total']),
        'track_num': track['track_number'],
        'artist': '/'.join(a['name'] for a in track['artists']),
        'album_artist': '/'.join(a['name'] for a in album['artists']),
        'album': track['album']['name'],
        # 'disc_num': track['disc_number'],
        'disc_num': (track['disc_number'], total_discs),
        'release_date': album['release_date'],
        'genre': ' ,'.join(album['genres']),
        'publisher': album['label'],
    }, {
        'track_id': track['id'],
        'image_url': track['album']['images'][0]['url']
    }


def perform_search(term):
    result = search_spotify(term)

    # if we don't find any result, attempt to simplify query by removing
    # things in brackets
    if not result:
        brackets = re.findall('\[.+?\]|\(.+?\)', term)

        while brackets and not result:
            term = term.replace(brackets.pop(), '')
            result = search_spotify(term)

    return result


def perform_analysis(track_id):
    features = sp.audio_features(track_id)[0]

    pitches = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

    return {
        'bpm': features['tempo'],
        'tkey': pitches[features['key']]
    }


def process(file, query, replace, rename, analyze, dry_run, magic, prompt, verbose):
    path = pathlib.Path(file).absolute()
    audio_file = eyed3.load(str(path))
    tag = audio_file.tag

    if query:
        search_term = query
    elif tag and tag.artist and tag.title:
        # prefer to use existing tags and fall back to filename
        search_term = '{} {}'.format(tag.artist, tag.title)
    else:
        search_term = path.stem

    if verbose:
        info_before = utils.file_info_to_string(audio_file, tag)

    # need a way to roll this back in case we get an exception further down..
    if not dry_run and (replace or not tag):
        audio_file.initTag(version=eyed3.id3.ID3_V2_3)
        tag = audio_file.tag


    # tag_data contains items that directly map to id3 tags
    # stuff in meta requires some processing
    tag_data, meta = perform_search(search_term)

    if prompt and search_term != '{} {}'.format(tag_data['artist'], tag_data['title']):
        click.echo('File: {}'.format(audio_file.path))
        click.echo('Search term used: {}'.format(search_term))
        click.echo('Found on spotify: {} - {}'.format(tag_data['artist'], tag_data['title']))
        if not click.confirm('Continue with re-tagging?', default=True):
            return
        
    for key, val in tag_data.items():
        if val:
            setattr(tag, key, val)

    # having to set year separately, though I think it should actually be set
    # by setting release_date
    tag.setTextFrame('TYER', str(tag.release_date.year))

    image_res = requests.get(meta['image_url'])

    if image_res.ok:
        tag.images.set(
            ImageFrame.FRONT_COVER,
            image_res.content,
            image_res.headers['Content-Type']
        )

    if analyze:
        analysis_results = perform_analysis(meta['track_id'])
        tag.bpm = analysis_results['bpm']
        tag.setTextFrame('TKEY', analysis_results['tkey'])

    if not dry_run:
        tag.save(str(path))

    new_name = TagTemplate(rename).substitute(tag, zeropad=True) if rename else None

    if rename and not dry_run:
        try:
            audio_file.rename(new_name)
            path = pathlib.Path(audio_file.path).absolute()
            printWarning('Renamed {} to {}'.format(str(path), audio_file.path))
        except IOError as ex:
            printError(str(ex))

    if verbose:
        info_after = utils.file_info_to_string(audio_file, tag, new_name=new_name)
        click.echo(''.join(utils.diff(info_before, info_after)))

if __name__ == '__main__':
    main()
