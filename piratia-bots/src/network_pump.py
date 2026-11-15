"""Independent native ping/receive pump; only the AI thread mutates the world.

Never drops or reorders world packets. A bounded overflow reconnects normally
and rebuilds authoritative state, rather than silently losing inventory updates.
"""
import queue,socket,threading,time

class NetworkPump:
    def __init__(self,client,max_packets=4096,max_bytes=2*1024*1024):
        self.client=client;self.queue=queue.Queue(max_packets);self.max_bytes=max_bytes
        self.lock=threading.Lock();self.bytes=0;self.peak_bytes=0;self.frames=0;self.pings=0
        self.error=None;self.stopping=threading.Event();self.thread=None;self.max_age=0
    def start(self):
        self.client.wire.background_reader_active=True
        self.thread=threading.Thread(target=self.run,name='piratia-network',daemon=True);self.thread.start();return self
    def run(self):
        try:
            while not self.stopping.is_set():
                try:command,payload=self.client.wire.receive(time.monotonic()+.25)
                except TimeoutError:
                    if time.monotonic()-self.client.wire.last_send>2:self.client.wire.heartbeat()
                    continue
                self.frames+=1
                if command in (515,537):
                    self.client.service(command,payload);self.pings+=1;continue
                with self.lock:
                    if self.bytes+len(payload)>self.max_bytes:raise ConnectionError('Очередь сетевых событий переполнена; повторный вход для синхронизации')
                    self.bytes+=len(payload);self.peak_bytes=max(self.peak_bytes,self.bytes)
                try:self.queue.put_nowait((command,payload,time.monotonic()))
                except queue.Full:raise ConnectionError('Слишком много необработанных сетевых событий; повторная синхронизация')
                if time.monotonic()-self.client.wire.last_send>2:self.client.wire.heartbeat()
        except Exception as error:
            if not self.stopping.is_set():self.error=error
    def receive(self,deadline):
        if self.error:raise self.error
        try:command,payload,created=self.queue.get(timeout=max(0,deadline-time.monotonic()))
        except queue.Empty:
            if self.error:raise self.error
            raise TimeoutError('No queued game event')
        with self.lock:self.bytes-=len(payload)
        self.max_age=max(self.max_age,time.monotonic()-created)
        return command,payload
    def close(self):
        self.stopping.set()
        if self.thread:self.thread.join(.8)
        if self.thread and self.thread.is_alive():
            try:self.client.wire.sock.shutdown(socket.SHUT_RDWR)
            except OSError:pass
            self.thread.join(.3)
        self.client.wire.background_reader_active=False
    def summary(self):
        return {'enabled':True,'received_frames':self.frames,'ping_answers':self.pings,'queued_events':self.queue.qsize(),
                'queued_bytes':self.bytes,'peak_queued_bytes':self.peak_bytes,'maximum_event_age_seconds':round(self.max_age,3),
                'error_type':type(self.error).__name__ if self.error else None,'world_modified_only_by_ai_thread':True}

def start_pump(client):
    return NetworkPump(client).start() if isinstance(getattr(client.wire,'sock',None),socket.socket) else None
