from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')


def rep(old, new, label):
    global s
    if old not in s:
        raise SystemExit(f'{label}: target not found')
    s = s.replace(old, new, 1)


# Track a draft-level 404 so a bad saved ID cannot hammer Sleeper forever.
rep(
'''  let picksBusy = false;\n  let draftBusy = false;\n  let eventQueue = [];''',
'''  let picksBusy = false;\n  let draftBusy = false;\n  let draftNotFound = false;\n  let eventQueue = [];''',
'draft not found state'
)


# Validate a candidate against Sleeper before we ever replace the shared draft.
rep(
'''  async function apiGet(path){\n    const r = await fetch(cb(API+path),{cache:"no-store",credentials:"omit",headers:{"Accept":"application/json"}});\n    if(!r.ok) throw new Error(`Sleeper API ${r.status}`);\n    lastApiAt=Date.now();\n    return r.json();\n  }''',
'''  async function apiGet(path){\n    const r = await fetch(cb(API+path),{cache:"no-store",credentials:"omit",headers:{"Accept":"application/json"}});\n    if(!r.ok) throw new Error(`Sleeper API ${r.status}`);\n    lastApiAt=Date.now();\n    return r.json();\n  }\n\n  async function validateDraftCandidate(id){\n    const r=await fetch(cb(`${API}/draft/${encodeURIComponent(id)}`),{cache:"no-store",credentials:"omit",headers:{"Accept":"application/json"}});\n    if(r.status===404)throw new Error(`Sleeper does not recognize draft ${id}. Nothing was saved.`);\n    if(!r.ok)throw new Error(`Sleeper draft check failed with HTTP ${r.status}. Nothing was saved.`);\n    const d=await r.json();\n    if(!d || String(d.draft_id||"")!==String(id))throw new Error(`Sleeper returned an invalid draft response for ${id}. Nothing was saved.`);\n    return d;\n  }''',
'candidate validation'
)


# Same-origin config is authoritative on load. A stale pending-session override
# caused an invalid draft to survive even after config.json was repaired.
old_pending='''        // Immediately after saving a new draft, Pages may still serve the old\n        // config for a few seconds. Keep the saving browser on the new draft for\n        // this one session; once the shared config catches up, discard the hint.\n        let pending="";\n        try{pending=String(sessionStorage.getItem(PENDING_DRAFT_SESSION_KEY)||"").trim()}catch(_){}\n        if(pending){\n          if(String(cfg?.draftId||"")===pending){\n            try{sessionStorage.removeItem(PENDING_DRAFT_SESSION_KEY)}catch(_){}\n          }else{\n            draftId=pending;\n            broadcastNames={};\n            absentUsernames=new Set();\n            autodraftUsernames=new Set();\n            debugLog("CONFIG",`using just-saved draft ${pending} while ${label} catches up`);\n          }\n        }\n\n'''
rep(old_pending, '''        // Shared config is the only draft source on startup. Clear any stale\n        // one-session override left by older builds.\n        try{sessionStorage.removeItem(PENDING_DRAFT_SESSION_KEY)}catch(_){}\n\n''', 'remove stale pending override')


# A missing draft gets one clear failure instead of hundreds of 404s.
rep(
'''  async function pollDraft(){\n    if(draftBusy)return;draftBusy=true;''',
'''  async function pollDraft(){\n    if(draftNotFound)return;\n    if(draftBusy)return;draftBusy=true;''',
'poll draft guard'
)

rep(
'''    }catch(e){$("status").textContent=`Draft API error: ${e.message}`;$("status").classList.add("bad");}\n    finally{draftBusy=false;}\n  }\n\n  async function pollPicks(){\n    if(picksBusy)return;picksBusy=true;''',
'''    }catch(e){\n      if(String(e?.message||e).includes("Sleeper API 404")){\n        draftNotFound=true;\n        const msg=`Sleeper does not recognize draft ${draftId}. Change the draft in Settings.`;\n        $("status").textContent=msg;$("status").classList.add("bad");\n        debugLogOnce(`draft404:${draftId}`,"DRAFT!",msg);\n      }else{\n        $("status").textContent=`Draft API error: ${e.message}`;$("status").classList.add("bad");\n      }\n    }\n    finally{draftBusy=false;}\n  }\n\n  async function pollPicks(){\n    if(draftNotFound)return;\n    if(picksBusy)return;picksBusy=true;''',
'404 stop loop'
)


# Validate first, save second, then switch the live page in-place. No immediate
# reload means GitHub Pages deploy lag cannot bounce us back to an old draft.
old_load='''  async function loadDraft(v){\n    const m=String(v||"").match(/(\\d{10,})/);\n    if(!m){\n      $("status").textContent="Enter a valid Sleeper draft URL or draft ID.";\n      $("status").classList.add("bad");\n      return;\n    }\n    const nextDraftId=m[1];\n    const draftChanged=nextDraftId!==draftId;\n    draftId=nextDraftId;\n\n    if(draftChanged){\n      broadcastNames={};\n      absentUsernames=new Set();\n      autodraftUsernames=new Set();\n      roastDecks.clear();\n      debugLog("CONFIG",`new draft ${draftId}: cleared broadcast names, absent flags and auto-draft flags`);\n    }\n\n    roastLevel=$("roastLevel").value;\n    await saveSharedSettings({reload:true});\n  }'''
new_load='''  async function loadDraft(v){\n    const m=String(v||"").match(/(\\d{10,})/);\n    if(!m){\n      $("status").textContent="Enter a valid Sleeper draft URL or draft ID.";\n      $("status").classList.add("bad");\n      return;\n    }\n\n    const nextDraftId=m[1];\n    $("status").classList.remove("bad");\n    $("status").textContent=`Checking Sleeper draft ${nextDraftId}…`;\n\n    let checkedDraft;\n    try{\n      checkedDraft=await validateDraftCandidate(nextDraftId);\n    }catch(e){\n      const msg=e?.message||String(e);\n      $("status").textContent=msg;\n      $("status").classList.add("bad");\n      debugLog("DRAFT!",msg);\n      return;\n    }\n\n    const draftChanged=nextDraftId!==draftId;\n    draftId=nextDraftId;\n    draftNotFound=false;\n\n    if(draftChanged){\n      broadcastNames={};\n      absentUsernames=new Set();\n      autodraftUsernames=new Set();\n      roastDecks.clear();\n      debugLog("CONFIG",`new draft ${draftId}: cleared broadcast names, absent flags and auto-draft flags`);\n    }\n\n    roastLevel=$("roastLevel").value;\n    const saved=await saveSharedSettings({reload:false});\n    if(!saved)return;\n\n    // Switch the running app immediately. GitHub Pages can update whenever it\n    // updates; the saving browser does not need to reload through stale config.\n    stopAudioGroup("warning");\n    hidePressure();\n    draft=checkedDraft;\n    picks=[];\n    users={};\n    leagueUsers={};\n    lastPickCount=null;\n    observedPickAt=null;\n    lastLivePickKey="";\n    currentLiveOrdinal=1;\n    marketReady=false;\n    adpRows=[];\n    sleeperAdpById={};\n    adpAttemptedFor="";\n    turnStartedAt=Date.now();\n    warningCrowdStarted=false;\n    $("draftInput").value=`https://sleeper.com/draft/nfl/${draftId}`;\n    $("settings").classList.remove("open");\n    debugLog("DRAFT",`validated and switched to ${draftId} · status ${draft?.status||"unknown"}`);\n    renderAll();\n    hydrate();\n    loadSleeperADP();\n    pollPicks();\n  }'''
rep(old_load, new_load, 'safe draft switching')

p.write_text(s, encoding='utf-8')
print('validated draft saves, removed stale override, and stopped 404 polling loops')
