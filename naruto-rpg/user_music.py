"""User soundtrack, exact generated MP3 imports and chapter-local repeating playlists."""
from pathlib import Path
import json
ROOT=Path(__file__).parent
DATA=json.loads((ROOT/'src/user-music.json').read_text())
def catalog():return DATA['tracks']+DATA['preservedTracks']
def runtime_data():
 tracks={r['key']:r for r in catalog()};audio={r['path']:i for i,r in enumerate(json.loads((ROOT/'src/all-original-audio.json').read_text()))}
 result=[];cache={};cursor=0;used=set()
 for chapter in DATA['chapters']:
  key=tuple(chapter['tracks']);j=chapter['chapter'];first=tracks[key[0]]
  if key not in cache:
   cache[key]=cursor
   for name in key:
    r=tracks[name];used.add(name);result += [f'    set MusicTrackPath[{cursor}]='+json.dumps(r['path']),f'    set MusicTrackSeconds[{cursor}]={r["duration_ms"]/1000.}'];cursor+=1
  result += [f'    set MusicChapterStart[{j}]={cache[key]}',f'    set MusicChapterCount[{j}]={len(key)}',f'    set PlaylistAudio[{j}]={audio.get(first["path"],-1)}',f'    set PlaylistDuration[{j}]={first["duration_ms"]/1000.}']
 for r in catalog():
  if r['key']not in used:
   result += [f'    set MusicTrackPath[{cursor}]='+json.dumps(r['path']),f'    set MusicTrackSeconds[{cursor}]={r["duration_ms"]/1000.}'];cursor+=1;used.add(r['key'])
 result.append(f'    set MusicTotal58={cursor}')
 return result
