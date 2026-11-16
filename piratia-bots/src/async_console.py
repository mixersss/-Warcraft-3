"""Bounded best-effort console output; Windows console pauses must not pause AI."""
import builtins
import queue
import threading


class AsyncConsole:
    def __init__(self, writer=None, limit=512):
        self.writer=writer or builtins.print
        self.queue=queue.Queue(limit);self.lock=threading.Lock();self.thread=None
        self.dropped=0;self.errors=0

    def emit(self,*args,**kwargs):
        # Materialize worker-owned objects before handing them to another thread.
        text=kwargs.get('sep',' ').join(map(str,args))
        options={k:v for k,v in kwargs.items() if k in ('end','flush','file')}
        with self.lock:
            if self.thread is None:
                self.thread=threading.Thread(target=self.run,name='piratia-console',daemon=True)
                self.thread.start()
        try:self.queue.put_nowait((text,options))
        except queue.Full:self.dropped+=1

    def run(self):
        while True:
            text,options=self.queue.get()
            try:self.writer(text,**options)
            except (OSError,ValueError):self.errors+=1
            finally:self.queue.task_done()


CONSOLE=AsyncConsole()
