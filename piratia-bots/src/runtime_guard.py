"""Safe local-state checks; never expose saved names or encrypted credentials."""
import json
from pathlib import Path


def inspect_data(path):
    data=Path(path)
    state=data/'bot-local.json'
    if not state.exists():
        if (data/'data'/'bot-local.json').exists():
            raise RuntimeError('Папка data вложена в другую data. Перенеси её содержимое на один уровень выше; новые аккаунты не созданы.')
        if (data/'bot-roles.json').exists() or any(data.glob('hunt-learning-*.json')):
            raise RuntimeError('Перенесена только часть data: нет bot-local.json с аккаунтами. Верни полную папку data из предыдущей версии; новые аккаунты не созданы.')
        return {'saved_state':False,'saved_bots':0}
    try:
        value=json.loads(state.read_text(encoding='utf-8-sig'))
        if value.get('version')!=1 or not isinstance(value.get('bots'),list):raise ValueError()
    except (OSError,ValueError,AttributeError):
        raise RuntimeError('Не удалось прочитать data/bot-local.json. Сохрани папку и верни её исправную копию; новые аккаунты не созданы.') from None
    return {'saved_state':True,'saved_bots':len(value['bots'])}


def require_population(path,count,allow_new=False):
    status=inspect_data(path)
    if not allow_new and (not status['saved_state'] or status['saved_bots']<count):
        raise RuntimeError('Текущие боты не найдены в полном количестве. Верни прежнюю папку data '
                           'или выбери --count не больше сохранённого числа. Новые аккаунты не созданы. '
                           'Только для намеренного создания новых ботов: --allow-new-bots.')
    return status


class SessionGuard:
    """One new launcher per Windows session/Gate port, even in copied folders."""
    def __init__(self,port):
        import ctypes
        from ctypes import wintypes
        self.api=ctypes.WinDLL('kernel32',use_last_error=True)
        self.api.CreateMutexW.argtypes=[wintypes.LPVOID,wintypes.BOOL,wintypes.LPCWSTR]
        self.api.CreateMutexW.restype=wintypes.HANDLE
        self.api.CloseHandle.argtypes=[wintypes.HANDLE]
        self.api.CloseHandle.restype=wintypes.BOOL
        self.handle=self.api.CreateMutexW(None,False,f'Local\\PiratiaHeadlessBots_{port}')
        if not self.handle:raise OSError('Не удалось установить защиту от повторного запуска.')
        if ctypes.get_last_error()==183:
            self.close()
            raise RuntimeError('Боты уже запущены из другой папки. Останови предыдущее окно перед запуском этой версии.')
    def close(self):
        if self.handle:self.api.CloseHandle(self.handle);self.handle=None
