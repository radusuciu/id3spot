# id3spot

A small script which uses data from Spotify to write id3 tags to mp3 files. I use it like so: `python id3spot.py -x *.mp3`.

#### Help Text:
```
Usage: id3spot.py [OPTIONS] [FILES]...

Options:
  -q, --query TEXT   Specify a query to use when searching for a matching
                     track.
  -r, --replace      Replace original tags entirely
  -R, --rename TEXT  Rename file (the extension is not affected) based on data
                     in the tag using substitution variables: $album,
                     $album_artist, $artist, $best_date,
                     $best_date:prefer_recording,
                     $best_date:prefer_recording:year,
                     $best_date:prefer_release,
                     $best_date:prefer_release:year, $best_date:year,
                     $disc:num, $disc:total, $file, $file:ext,
                     $original_release_date, $original_release_date:year,
                     $recording_date, $recording_date:year, $release_date,
                     $release_date:year, $title, $track:num, $track:total
  -a, --analyze      Include ID3 tags for bpm and key from Spotify.
  -d, --dry-run      Perform lookup but do not write tags.
  -x, --magic        Shortcut for id3spot.py -arpR "$artist - $title"
  -p, --prompt       If song is not exact match, prompt before using
                     information.
  -v, --verbose      Output diff for each file processed.
  --help             Show this message and exit.
```
