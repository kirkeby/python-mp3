__all__ = ['id3tag', 'load']

import v1
import neds_id3reader

no_tag = {
    'title': None,
    'artist': None,
    'album': None,
    'year': None,
    'comment': None,
    'track': None,
    'genre': None,
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
    if v1tag:
        w.update(v1tag)
    try:
        tag['track'] = int(tag['track'])
    except:
        tag['track'] = 0
    for k, v in tag.items():
        if v:
            w[k] = v
    for k in w:
        if not isinstance(w[k], str):
            continue
        if k == 'path':
            break
        for encoding in [None, 'utf-8', 'iso-8859-1']:
            try:
                w[k] = w[k].decode(encoding)
                break
            except:
                pass
        else:
            w[k] = w[k].decode('ascii', 'replace')

    return w

def load(path, **kwargs):
    return id3tag(open(path), path=path, **kwargs)
