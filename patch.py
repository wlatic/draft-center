from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')


def rep(old, new, label):
    global s
    if old not in s:
        raise SystemExit(f'{label}: target not found')
    s = s.replace(old, new, 1)


rep(
'''  const SHARED_CONFIG_URL = "https://raw.githubusercontent.com/wlatic/draft-center/main/config.json";\n  const GITHUB_CONFIG_API = "https://api.github.com/repos/wlatic/draft-center/contents/config.json";''',
'''  // Read shared settings from the same GitHub Pages site first. This avoids\n  // making raw.githubusercontent.com a hard dependency during startup.\n  const SHARED_CONFIG_URL = new URL("config.json", window.location.href).toString();\n  const SHARED_CONFIG_FALLBACK_URL = "https://raw.githubusercontent.com/wlatic/draft-center/main/config.json";\n  const GITHUB_CONFIG_API = "https://api.github.com/repos/wlatic/draft-center/contents/config.json";''',
'shared config URLs'
)

old_load = '''  async function loadSharedSettings(){\n    try{\n      const r=await fetch(`${SHARED_CONFIG_URL}?v=${Date.now()}`,{cache:"no-store"});\n      if(!r.ok)throw new Error(`config ${r.status}`);\n      const cfg=await r.json();\n      applySharedSettings(cfg);\n      debugLog("CONFIG",`loaded shared config: draft ${draftId}, ${Object.keys(broadcastNames).length} names, ${absentUsernames.size} absent, ${autodraftUsernames.size} auto`);\n      updateSharedConfigSummary();\n    }catch(e){\n      console.warn("Shared DraftCenter config unavailable; using defaults",e);\n    }\n  }'''

new_load = '''  async function fetchJsonWithTimeout(url,timeoutMs=3500){\n    const sep=url.includes("?")?"&":"?";\n    let timer;\n    const timeout=new Promise((_,reject)=>{\n      timer=setTimeout(()=>reject(new Error(`timeout after ${timeoutMs}ms`)),timeoutMs);\n    });\n    try{\n      const request=fetch(`${url}${sep}v=${Date.now()}`,{cache:"no-store",credentials:"omit"}).then(async r=>{\n        if(!r.ok)throw new Error(`HTTP ${r.status}`);\n        return r.json();\n      });\n      return await Promise.race([request,timeout]);\n    }finally{\n      clearTimeout(timer);\n    }\n  }\n\n  async function loadSharedSettings(){\n    const sources=[\n      ["GitHub Pages",SHARED_CONFIG_URL],\n      ["GitHub raw fallback",SHARED_CONFIG_FALLBACK_URL]\n    ];\n\n    for(const [label,url] of sources){\n      try{\n        const cfg=await fetchJsonWithTimeout(url);\n        applySharedSettings(cfg);\n        debugLog("CONFIG",`loaded from ${label}: draft ${draftId}, ${Object.keys(broadcastNames).length} names, ${absentUsernames.size} absent, ${autodraftUsernames.size} auto`);\n        updateSharedConfigSummary();\n        return true;\n      }catch(e){\n        console.warn(`DraftCenter config via ${label} failed`,e);\n      }\n    }\n\n    debugLog("CONFIG!",`shared config unavailable; continuing with default draft ${draftId}`);\n    updateSharedConfigSummary();\n    return false;\n  }'''
rep(old_load, new_load, 'shared config loader')

old_boot = '''  async function boot(){\n    // Shared league settings are loaded once per page load. There is deliberately\n    // no config polling: refresh another device when you want it to pick up changes.\n    await loadSharedSettings();\n    debugLog("BOOT",`DraftCenter session started for ${draftId}`);\n    $("draftInput").value=`https://sleeper.com/draft/nfl/${draftId}`;\n    pollDraft();pollPicks();\n    // ADP load is started after the first draft object arrives so we can choose\n    // the correct scoring format. pollDraft() will trigger it once below.\n    setInterval(pollDraft,DRAFT_MS);\n    setInterval(pollPicks,PICKS_MS);\n    setInterval(renderClock,100);\n    setInterval(eventTick,100);\n    setInterval(rotateInsight,10000);\n  }'''

new_boot = '''  async function boot(){\n    // Shared league settings are loaded once per page load. There is deliberately\n    // no config polling: refresh another device when you want it to pick up changes.\n    $("status").textContent="Loading shared DraftCenter settings…";\n    await loadSharedSettings();\n    debugLog("BOOT",`DraftCenter session started for ${draftId}`);\n    $("draftInput").value=`https://sleeper.com/draft/nfl/${draftId}`;\n    $("status").textContent=`Connecting to Sleeper draft ${draftId}…`;\n\n    // Start Sleeper immediately after the bounded config read. A slow/blocked\n    // config host can no longer leave the whole TV UI stuck on CONNECTING.\n    pollDraft();\n    pollPicks();\n\n    setTimeout(()=>{\n      if(draft)return;\n      const msg=`Still waiting for Sleeper draft ${draftId}. Open Settings → Debug for the exact startup error.`;\n      $("status").textContent=msg;\n      $("status").classList.add("bad");\n      $("board-subtitle").textContent=`Unable to load draft ${draftId}`;\n      $("api-state").innerHTML='<span class="dot"></span><span>Connection problem</span>';\n      debugLog("BOOT!",msg);\n    },6000);\n\n    // ADP load is started after the first draft object arrives so we can choose\n    // the correct scoring format. pollDraft() will trigger it once below.\n    setInterval(pollDraft,DRAFT_MS);\n    setInterval(pollPicks,PICKS_MS);\n    setInterval(renderClock,100);\n    setInterval(eventTick,100);\n    setInterval(rotateInsight,10000);\n  }'''
rep(old_boot, new_boot, 'boot watchdog')

p.write_text(s, encoding='utf-8')
print('patched startup config loading and watchdog')
