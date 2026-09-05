from pathlib import Path

p = Path("index.html")
s = p.read_text(encoding="utf-8")

old = '''  /* High-contrast TV palette: positions should read instantly from across a room. */
  --qb:#60a5fa;
  --rb:#34d399;
  --wr:#f59e0b;
  --te:#a78bfa;
  --k:#fde047;
  --def:#f87171;
  --other:#a9c4d8;'''
new = '''  /* TV palette: preserve Sleeper's familiar position families, but increase separation. */
  --qb:#ee9dca;
  --rb:#45d6a8;
  --wr:#38bdf8;
  --te:#f0c266;
  --k:#b6a2ed;
  --def:#f5a45d;
  --other:#a9c4d8;'''

if old not in s:
    raise SystemExit("TV palette block not found")
s = s.replace(old, new, 1)

s = s.replace(
    "High Contrast TV separates RB green and WR amber so they remain obvious from across the room. This setting is saved only on this device/browser.",
    "High Contrast TV keeps Sleeper's familiar position color families, but pushes RB greener-teal and WR brighter blue so they remain obvious from across the room. This setting is saved only on this device/browser.",
    1,
)

p.write_text(s, encoding="utf-8")
print("refined TV palette while preserving Sleeper color families")
