from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')


def rep(old, new, label):
    global s
    if old not in s:
        raise SystemExit(f'{label}: target not found')
    s = s.replace(old, new, 1)


# -----------------------------------------------------------------------------
# Never play the exact same selectable sound twice in a row, even when two
# different sound decks overlap (for example pressure vs timeout reactions).
# The clock currently has only one click recording, so it remains the only
# unavoidable repeat until that pool is expanded.
# -----------------------------------------------------------------------------
rep(
'''  function chooseSound(tags,deckKey=null){\n    const matches=soundsWithTags(tags);\n    if(!matches.length)return null;\n    const key=deckKey||tags.join(":");\n    let deck=soundDecks.get(key)||[];\n    deck=deck.filter(id=>matches.some(s=>s.id===id));\n    if(!deck.length){\n      deck=shuffledSounds(matches).map(s=>s.id);\n      const previous=soundRecentIds[soundRecentIds.length-1];\n      if(deck.length>1 && deck[0]===previous){\n        [deck[0],deck[1]]=[deck[1],deck[0]];\n      }\n    }\n    const id=deck.shift();\n    soundDecks.set(key,deck);\n    return matches.find(s=>s.id===id)||matches[0];\n  }''',
'''  function chooseSound(tags,deckKey=null){\n    const matches=soundsWithTags(tags);\n    if(!matches.length)return null;\n    const key=deckKey||tags.join(":");\n    const previous=soundRecentIds[soundRecentIds.length-1]||"";\n    let deck=soundDecks.get(key)||[];\n    deck=deck.filter(id=>matches.some(s=>s.id===id));\n    if(!deck.length)deck=shuffledSounds(matches).map(s=>s.id);\n\n    // Global no-immediate-repeat rule. This is checked on EVERY selection, not\n    // only when a deck is refilled, because reaction pools can overlap across\n    // pressure/timeout/test decks.\n    if(matches.length>1 && deck[0]===previous){\n      const altIndex=deck.findIndex(id=>id!==previous);\n      if(altIndex>0){\n        [deck[0],deck[altIndex]]=[deck[altIndex],deck[0]];\n      }else{\n        // If this deck has only the previous clip left, borrow a fresh\n        // alternative now and postpone the repeat until later.\n        const alternatives=shuffledSounds(matches.filter(s=>s.id!==previous)).map(s=>s.id);\n        deck=[...alternatives,...deck];\n      }\n    }\n\n    const id=deck.shift();\n    soundDecks.set(key,deck);\n    return matches.find(s=>s.id===id)||matches[0];\n  }''',
'global consecutive sound guard'
)


# -----------------------------------------------------------------------------
# Load the candidate draft's picks BEFORE switching the UI. Previously we set
# picks=[] and rendered immediately, which made every newly entered draft flash
# back to Round 1 until the next picks poll arrived.
# -----------------------------------------------------------------------------
rep(
'''  async function validateDraftCandidate(id){\n    const r=await fetch(cb(`${API}/draft/${encodeURIComponent(id)}`),{cache:"no-store",credentials:"omit",headers:{"Accept":"application/json"}});\n    if(r.status===404)throw new Error(`Sleeper does not recognize draft ${id}. Nothing was saved.`);\n    if(!r.ok)throw new Error(`Sleeper draft check failed with HTTP ${r.status}. Nothing was saved.`);\n    const d=await r.json();\n    if(!d || String(d.draft_id||"")!==String(id))throw new Error(`Sleeper returned an invalid draft response for ${id}. Nothing was saved.`);\n    return d;\n  }''',
'''  async function validateDraftCandidate(id){\n    const r=await fetch(cb(`${API}/draft/${encodeURIComponent(id)}`),{cache:"no-store",credentials:"omit",headers:{"Accept":"application/json"}});\n    if(r.status===404)throw new Error(`Sleeper does not recognize draft ${id}. Nothing was saved.`);\n    if(!r.ok)throw new Error(`Sleeper draft check failed with HTTP ${r.status}. Nothing was saved.`);\n    const d=await r.json();\n    if(!d || String(d.draft_id||"")!==String(id))throw new Error(`Sleeper returned an invalid draft response for ${id}. Nothing was saved.`);\n    return d;\n  }\n\n  async function fetchDraftCandidatePicks(id){\n    const r=await fetch(cb(`${API}/draft/${encodeURIComponent(id)}/picks`),{cache:"no-store",credentials:"omit",headers:{"Accept":"application/json"}});\n    if(!r.ok)throw new Error(`Sleeper picks check failed with HTTP ${r.status}. Nothing was saved.`);\n    const arr=await r.json();\n    if(!Array.isArray(arr))throw new Error(`Sleeper returned an invalid picks response for ${id}. Nothing was saved.`);\n    return arr.slice().sort((a,b)=>Number(a.pick_no||0)-Number(b.pick_no||0));\n  }''',
'candidate pick preload helper'
)

rep(
'''    let checkedDraft;\n    try{\n      checkedDraft=await validateDraftCandidate(nextDraftId);\n    }catch(e){''',
'''    let checkedDraft, checkedPicks;\n    try{\n      checkedDraft=await validateDraftCandidate(nextDraftId);\n      checkedPicks=await fetchDraftCandidatePicks(nextDraftId);\n    }catch(e){''',
'preload candidate picks'
)

rep(
'''    draft=checkedDraft;\n    picks=[];\n    users={};\n    leagueUsers={};\n    lastPickCount=null;\n    observedPickAt=null;\n    lastLivePickKey="";\n    currentLiveOrdinal=1;''',
'''    draft=checkedDraft;\n    // Install draft + picks atomically so current round/turn is correct on the\n    // very first render after changing URLs.\n    picks=checkedPicks;\n    users={};\n    leagueUsers={};\n    lastPickCount=checkedPicks.length;\n    observedPickAt=null;\n    const initialLive=checkedPicks.filter(p=>!isKeeperPick(p));\n    lastLivePickKey=initialLive.length?pickCellKey(initialLive[initialLive.length-1]):"";\n    currentLiveOrdinal=1;''',
'atomic draft and picks switch'
)

p.write_text(s, encoding='utf-8')
print('fixed round switch flash and consecutive sound repeats')
