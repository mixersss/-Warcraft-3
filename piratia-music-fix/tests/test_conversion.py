"""Real synthetic MP3 -> Vorbis conversions, resumable backups and exact restoration."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import convert_music as music


class ConversionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ffmpeg=shutil.which('ffmpeg');cls.ffprobe=shutil.which('ffprobe')
        if not cls.ffmpeg or not cls.ffprobe:raise unittest.SkipTest('FFmpeg and ffprobe are required')
        cls.audio=tempfile.TemporaryDirectory()
        source=Path(cls.audio.name)/'tone.mp3'
        subprocess.run([cls.ffmpeg,'-v','error','-nostdin','-f','lavfi','-i','sine=frequency=440:duration=0.4',
                        '-ar','44100','-ac','2','-c:a','libmp3lame',str(source)],check=True,capture_output=True)
        cls.original=source.read_bytes()
    @classmethod
    def tearDownClass(cls):cls.audio.cleanup()
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.client=Path(self.tmp.name)/'Клиент с пробелами'
        for name in ('system','scripts','music/подпапка'):(self.client/name).mkdir(parents=True,exist_ok=True)
        (self.client/'system/Game.exe').write_bytes(b'unchanged synthetic game fixture')
        (self.client/'scripts/kop.cfg').write_bytes(b'[Sound]\r\nmusic = 1\r\n')
        self.paths=[self.client/'music/01.mp3',self.client/'music/подпапка/02.MP3']
        for p in self.paths:p.write_bytes(self.original)
        (self.client/'music/effect.wav').write_bytes(b'untouched sound fixture')
    def apply(self):return music.apply(self.client,self.ffmpeg,self.ffprobe,lambda _:None)
    def test_real_conversion_preserves_paths_duration_and_unrelated_files(self):
        self.assertEqual(self.apply(),(2,2))
        for p in self.paths:
            self.assertEqual(p.read_bytes()[:4],b'OggS')
            stream,duration=music.probe(p,self.ffprobe)
            self.assertEqual(stream['codec_name'],'vorbis')
            self.assertAlmostEqual(duration,.4,places=2)
            original=music.contained(self.client/music.BACKUP/'originals',p.relative_to(self.client))
            self.assertEqual(original.read_bytes(),self.original)
        self.assertEqual((self.client/'music/effect.wav').read_bytes(),b'untouched sound fixture')
        self.assertEqual((self.client/'scripts/kop.cfg').read_bytes(),b'[Sound]\r\nmusic = 1\r\n')
        self.assertEqual((self.client/'system/Game.exe').read_bytes(),b'unchanged synthetic game fixture')
    def test_restore_is_byte_exact_and_repeatable(self):
        self.apply();self.assertEqual(music.restore(self.client,lambda _:None),2)
        self.assertEqual(music.restore(self.client,lambda _:None),0)
        self.assertTrue(all(p.read_bytes()==self.original for p in self.paths))
    def test_repeat_apply_does_not_reencode_or_overwrite_backups(self):
        self.apply();before=[music.digest(p) for p in self.paths]
        with patch.object(music,'convert_one',side_effect=AssertionError('Must not reconvert')):
            self.assertEqual(self.apply(),(0,2))
        self.assertEqual([music.digest(p) for p in self.paths],before)
    def test_failed_conversion_keeps_original_and_can_resume(self):
        original_convert=music.convert_one;calls=[]
        def fail_second(*args):
            calls.append(True)
            if len(calls)==2:raise RuntimeError('Simulated interruption')
            return original_convert(*args)
        with patch.object(music,'convert_one',side_effect=fail_second):
            with self.assertRaises(RuntimeError):self.apply()
        self.assertEqual(self.paths[0].read_bytes()[:4],b'OggS')
        self.assertEqual(self.paths[1].read_bytes(),self.original)
        self.assertEqual(self.apply(),(1,2))
        music.restore(self.client,lambda _:None)
        self.assertTrue(all(p.read_bytes()==self.original for p in self.paths))
    def test_restore_preflights_all_files_and_refuses_external_edits(self):
        self.apply();first=self.paths[0].read_bytes();self.paths[1].write_bytes(b'external edit')
        with self.assertRaises(ValueError):music.restore(self.client,lambda _:None)
        self.assertEqual(self.paths[0].read_bytes(),first)
        self.assertEqual(self.paths[1].read_bytes(),b'external edit')
    def test_backup_corruption_is_not_overwritten(self):
        self.apply();backup=self.client/music.BACKUP/'originals/music/01.mp3';backup.write_bytes(b'corrupt')
        current=self.paths[0].read_bytes()
        with self.assertRaises(ValueError):self.apply()
        self.assertEqual(backup.read_bytes(),b'corrupt');self.assertEqual(self.paths[0].read_bytes(),current)
    def test_wrong_folder_and_unsafe_manifest_are_rejected(self):
        with self.assertRaises(ValueError):music.validate_client(self.client/'music')
        root=self.client/music.BACKUP;root.mkdir()
        music.save_manifest(root,{'version':1,'files':{'../outside':{'original':'0'*64,'converted':None}}})
        with self.assertRaises(ValueError):music.restore(self.client,lambda _:None)
        self.assertTrue(all(p.read_bytes()==self.original for p in self.paths))
    def test_existing_ogg_track_is_not_reencoded(self):
        music.convert_one(self.paths[0],self.client/'converted',self.ffmpeg,self.ffprobe)
        self.paths[0].write_bytes((self.client/'converted').read_bytes());original=self.paths[0].read_bytes()
        self.assertEqual(self.apply(),(1,2))
        self.assertEqual(self.paths[0].read_bytes(),original)
        self.assertEqual(music.restore(self.client,lambda _:None),1)
        self.assertEqual(self.paths[0].read_bytes(),original)
    def test_crash_after_manifest_before_replace_is_resumable(self):
        original_replace=music.os.replace;triggered=[]
        def fail_track(source,target):
            if Path(target)==self.paths[0] and not triggered:
                triggered.append(True);raise PermissionError('Simulated replacement failure')
            return original_replace(source,target)
        with patch.object(music.os,'replace',side_effect=fail_track):
            with self.assertRaises(PermissionError):self.apply()
        self.assertEqual(self.paths[0].read_bytes(),self.original)
        self.assertEqual(self.apply(),(2,2))


if __name__=='__main__':unittest.main()
