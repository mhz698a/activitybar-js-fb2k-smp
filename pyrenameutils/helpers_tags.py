# pyrenameutils.helpers_tags.py
# Mutagen-based tag reading/writing
try:
    from mutagen import File as MutagenFile
    from mutagen.id3 import ID3, ID3NoHeaderError, TIT2, TPE1, TALB, TDRC, TRCK, TCON, COMM
    from mutagen.mp4 import MP4, MP4Tags
except Exception:
    MutagenFile = None
    ID3 = ID3NoHeaderError = TIT2 = TPE1 = TALB = TDRC = TRCK = TCON = COMM = None
    MP4 = MP4Tags = None
    
def read_tags(path: str) -> dict:
    tags = {
        "title": "",
        "artist": "",
        "album": "",
        "date": "",
        "track": "",
        "genre": "",
        "comment": ""
    }
    if MutagenFile is None:
        return tags
    try:
        lower = path.lower()
        if lower.endswith('.mp3'):
            try:
                id3 = ID3(path)
            except ID3NoHeaderError:
                return tags
            if 'TIT2' in id3:
                tags['title'] = str(id3.get('TIT2'))
            if 'TPE1' in id3:
                tags['artist'] = str(id3.get('TPE1'))
            if 'TALB' in id3:
                tags['album'] = str(id3.get('TALB'))
            if 'TDRC' in id3:
                tags['date'] = str(id3.get('TDRC'))
            if 'TRCK' in id3:
                tags['track'] = str(id3.get('TRCK'))
            if 'TCON' in id3:
                frame = id3.get('TCON')
                tags['genre'] = frame.text[0] if frame and getattr(frame, "text", None) else ''
            comms = id3.getall('COMM')
            for c in comms:
                if c.desc == 'Comment':
                    tags['comment'] = c.text[0] if c.text else ''
                    break
                
        elif lower.endswith(('.mp4', '.m4a', '.m4v')):
            mp4 = MP4(path)
            if mp4.tags is None:
                return tags
            if '\xa9nam' in mp4.tags:
                tags['title'] = mp4.tags.get('\xa9nam', [''])[0]
            if '\xa9ART' in mp4.tags:
                tags['artist'] = mp4.tags.get('\xa9ART', [''])[0]
            if '\xa9alb' in mp4.tags:
                tags['album'] = mp4.tags.get('\xa9alb', [''])[0]
            if '\xa9day' in mp4.tags:
                tags['date'] = mp4.tags.get('\xa9day', [''])[0]
            if '\xa9gen' in mp4.tags:
                tags['genre'] = mp4.tags.get('\xa9gen', [''])[0]
            if 'trkn' in mp4.tags:
                t = mp4.tags['trkn'][0]
                if isinstance(t, tuple):
                    track, total = t
                    tags['track'] = f"{track:02d}/{total:02d}" if total else f"{track:02d}"
            if '\xa9cmt' in mp4.tags:
                tags['comment'] = mp4.tags.get('\xa9cmt', [''])[0]
    except Exception:
        pass
    return tags

def write_tags(path: str, title: str, artist: str, 
               comment: str, album: str, date: str, 
               track: str, genre: str):    
    if MutagenFile is None:
        raise RuntimeError("mutagen library not available. Install with: pip install mutagen")
    lower = path.lower()
    if lower.endswith('.mp3'):
        try:
            try:
                id3 = ID3(path)
            except ID3NoHeaderError:
                id3 = ID3()
            if title is not None:
                id3.delall('TIT2')
                if title:
                    id3.add(TIT2(encoding=3, text=title))
            if artist is not None:
                id3.delall('TPE1')
                if artist:
                    id3.add(TPE1(encoding=3, text=artist))
                    
            if album is not None:
                id3.delall('TALB')
                if album:
                    id3.add(TALB(encoding=3, text=album))
            if date is not None:
                id3.delall('TDRC')
                if date:
                    id3.add(TDRC(encoding=3, text=date))
            if track is not None:
                id3.delall('TRCK')
                if track:
                    id3.add(TRCK(encoding=3, text=track))     
            if genre is not None:
                id3.delall('TCON')
                if genre:
                    id3.add(TCON(encoding=3, text=genre))   
            if comment is not None:
                id3.delall('COMM')
                if comment:
                    id3.add(COMM(encoding=3, lang='eng', desc='Comment', text=comment))
            id3.save(path)
        except Exception:
            raise
    elif lower.endswith(('.mp4', '.m4a', '.m4v')):
        try:
            mp4 = MP4(path)
            tags = mp4.tags
            if tags is None:
                tags = MP4Tags()
                mp4.tags = tags
            
            if title is not None:
                if title:
                    tags['\xa9nam'] = [title]
                else:
                    tags.pop('\xa9nam', None)

            if artist is not None:
                if artist:
                    tags['\xa9ART'] = [artist]
                else:
                    tags.pop('\xa9ART', None)

            if album is not None:
                if album:
                    tags['\xa9alb'] = [album]
                else:
                    tags.pop('\xa9alb', None)

            if date is not None:
                if date:
                    tags['\xa9day'] = [date]
                else:
                    tags.pop('\xa9day', None)

            if track is not None:
                if track:
                    if '/' in track:
                        a, b = track.split('/', 1)
                        tags['trkn'] = [(int(a), int(b))]
                    else:
                        tags['trkn'] = [(int(track), 0)]
                else:
                    tags.pop('trkn', None)
            if genre is not None:
                if genre:
                    tags['\xa9gen'] = [genre]
                else:
                    tags.pop('\xa9gen', None)
            if comment is not None:
                if comment:
                    tags['\xa9cmt'] = [comment]
                else:
                    tags.pop('\xa9cmt', None)
            
            mp4.save()
        except Exception:
            raise
    else:
        raise RuntimeError("Formato no soportado para etiquetas: " + path)


