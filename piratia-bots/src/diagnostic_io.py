"""Best-effort atomic diagnostic snapshots; never suppress identity/state-store errors."""
import json,os,tempfile
from pathlib import Path

def write_snapshot(path,data):
    path=Path(path);temporary=None
    try:
        descriptor,name=tempfile.mkstemp(prefix=path.name+'.',suffix='.tmp',dir=path.parent);temporary=Path(name)
        with os.fdopen(descriptor,'w',encoding='utf8') as stream:
            json.dump(data,stream,ensure_ascii=False,indent=2);stream.write('\n')
        os.replace(temporary,path)
        return True
    except OSError:return False
    finally:
        if temporary is not None:
            try:temporary.unlink(missing_ok=True)
            except OSError:pass
