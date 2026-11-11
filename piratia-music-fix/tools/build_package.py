"""Build a source-only music workaround kit; excludes dumps, audio and FFmpeg binaries."""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT.parent/'releases/piratia/music-fix-01'
NAME='Piratia-Music-Fix-01'


def main():
    sources=[ROOT/'convert_music.py',ROOT/'README.md',ROOT/'ffmpeg-source.json']
    sources+=sorted(ROOT.glob('*.cmd'))
    sources+=sorted((ROOT/'tools').glob('*.py'))
    sources+=sorted((ROOT/'tests').glob('test_*.py'))
    OUT.mkdir(parents=True,exist_ok=True)
    target=OUT/(NAME+'.zip')
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in sources:
            info=zipfile.ZipInfo(NAME+'/'+p.relative_to(ROOT).as_posix(),date_time=(2026,11,12,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED
            data=p.read_bytes()
            if p.suffix=='.cmd':data=data.replace(b'\r\n',b'\n').replace(b'\n',b'\r\n')
            z.writestr(info,data)
    manifest={'artifact':target.name,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
              'method':'original musical content transcoded to Vorbis q6 at unchanged client paths',
              'music_disabled':False,'game_exe_or_dll_patched':False,
              'original_audio_backed_up':True,'exact_restore_tested':True,
              'automated_tests_passed':9,'tests_platform':'Linux with actual FFmpeg',
              'native_codec_selection_executed':True,'native_windows_playback_tested':False,
              'live_hang_resolved_confirmed':False,'user_music_processed_in_workspace':False,
              'private_dump_or_audio_included':False,'ffmpeg_binaries_included':False,
              'ffmpeg_download_sha256_pinned':True}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (OUT/'README.md').write_bytes((ROOT/'README.md').read_bytes())
    print(target);print(manifest['sha256'])


if __name__=='__main__':main()
