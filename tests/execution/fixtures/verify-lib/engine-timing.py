"""Both engines render a 128px preview headless; report wall seconds."""
import os
import time

import bpy

exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "state-snapshot.py")).read())

before = snapshot()
res = {}
for engine in ("EEVEE", "CYCLES"):
    t = time.time()
    p = preview_render(path=os.path.join(os.environ["AGENT_PREVIEW_DIR"],
                                         f"{engine.lower()}.png"),
                       res=128, samples=8, engine=engine)
    res[engine] = {"seconds": round(time.time() - t, 3),
                   "exists": os.path.exists(p),
                   "stdev": frame_stats(p)["stdev"]}

emit(engines=res, before=before, after=snapshot())
