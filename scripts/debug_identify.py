"""Print Super VL's full identify output for a few images (debugging recognition). Usage: python -m scripts.debug_identify FILE..."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from app.ai import tasks

for f in sys.argv[1:]:
    p = Path(f)
    out = tasks.identify([(p.read_bytes(), "image/png")], "", [])
    print(p.name, json.dumps({k: out[k] for k in ("category", "category_confidence", "brand", "product_name", "what_i_see")}))
