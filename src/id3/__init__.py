__all__ = ['id3tag', 'load']

import v1
import neds_id3reader

no_tag = {
    'title': '',
    'artist': '',
    'album': '',
    'year': '',
    'comment': '',
    'track': 0,
    'genre': '',
}

def id3tag(f, **kwargs):
    # Use Ned's ID3-reader to get basic tags
    id3r = neds_id3reader.Reader(f)
    tag = {
        'album': id3r.getValue('album'),
        'artist': id3r.getValue('performer'),
        'title': id3r.getValue('title'),
        'track': id3r.getValue('track'),
        'year': id3r.getValue('year'),
    }

    # Use own ID3-reader to get genre and comment
    v1tag = v1.id3tag(f)

    # Combine all the dicts
    w = {}
    w.update(no_tag)
    w.update(kwargs)
    w.update(v1tag)
    w.update(tag)
    return w

def load(path):
    return id3tag(open(path), path=path)
