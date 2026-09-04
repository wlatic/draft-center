from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')

old = '''  async function loadSharedSettings(){\n    const sources=[\n      ["GitHub Pages",SHARED_CONFIG_URL],\n      ["GitHub raw fallback",SHARED_CONFIG_FALLBACK_URL]\n    ];'''
new = '''  async function loadSharedSettings(){\n    // Raw main is the source of truth. GitHub Pages can lag behind config.json\n    // while a Pages deployment is rebuilding, which previously made a newly\n    // saved draft appear to revert to the previous draft on reload.\n    const sources=[\n      ["GitHub raw",SHARED_CONFIG_FALLBACK_URL],\n      ["GitHub Pages fallback",SHARED_CONFIG_URL]\n    ];'''

if old not in s:
    raise SystemExit('shared config source order target not found')
s = s.replace(old, new, 1)

old2 = '''      if(reload)setTimeout(()=>location.reload(),900);'''
new2 = '''      if(reload){\n        // Raw/main updates before the Pages deployment, so reload after a short\n        // commit-settle delay rather than waiting for GitHub Pages to rebuild.\n        setTimeout(()=>location.reload(),1400);\n      }'''
if old2 not in s:
    raise SystemExit('reload target not found')
s = s.replace(old2, new2, 1)

p.write_text(s, encoding='utf-8')
print('patched shared config source-of-truth ordering')
