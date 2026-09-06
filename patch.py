from pathlib import Path

p=Path('index.html')
s=p.read_text(encoding='utf-8')

def rep(old,new,label):
    global s
    if old not in s:
        raise SystemExit(f'{label}: target not found')
    s=s.replace(old,new,1)

rep(
'''    if(t.access && (!t.expires || Date.now()<t.expires))return t.access;\n    if(t.refresh){\n      const clientId=yahooClientId();\n      if(!clientId)throw new Error("Yahoo Client ID missing on this device.");\n      const data=await yahooTokenRequest({client_id:clientId,refresh_token:t.refresh,grant_type:"refresh_token"});''',
'''    if(t.access && t.expires && Date.now()<t.expires)return t.access;\n    if(t.refresh){\n      const clientId=yahooClientId();\n      if(!clientId)throw new Error("Yahoo Client ID missing on this device.");\n      const data=await yahooTokenRequest({client_id:clientId,redirect_uri:yahooCallbackUrl(),refresh_token:t.refresh,grant_type:"refresh_token"});''',
'yahoo refresh token'
)

rep(
'''    if(r.status===401 && retry){\n      try{localStorage.setItem("draftcenterYahooExpiresAt","0")}catch(_){}\n      return yahooApiText(path,false);\n    }\n    if(!r.ok)throw new Error(`Yahoo Fantasy API ${r.status}`);\n    return r.text();''',
'''    if(r.status===401 && retry){\n      try{localStorage.removeItem("draftcenterYahooAccessToken");localStorage.setItem("draftcenterYahooExpiresAt","0")}catch(_){}\n      return yahooApiText(path,false);\n    }\n    if(!r.ok)throw new Error(`Yahoo Fantasy API ${r.status}`);\n    lastApiAt=Date.now();\n    return r.text();''',
'yahoo api refresh'
)

rep(
'''    const maxRound=raw.reduce((m,x)=>Math.max(m,x.round||0),0);\n    return Math.max(total,maxRound,15);''',
'''    const maxRound=raw.reduce((m,x)=>Math.max(m,x.round||0),0);\n    const resolved=Math.max(total,maxRound);\n    return resolved>0?resolved:15;''',
'yahoo rounds'
)

rep(
'''    if(Date.now()-yahooLastDraftPollAt<8000)return;''',
'''    if(Date.now()-yahooLastDraftPollAt<30000)return;''',
'yahoo draft throttle'
)

rep(
'''  $("draftProvider").addEventListener("change",e=>{\n    draftProvider=e.currentTarget.value==="yahoo"?"yahoo":"sleeper";\n    updateProviderUI();\n  });''',
'''  $("draftProvider").addEventListener("change",()=>{\n    // This is only an editor choice until Save shared draft succeeds. Do not\n    // interrupt the currently running provider just because Settings changed.\n    updateYahooAuthUI();\n  });''',
'provider selector safety'
)

rep(
'''    $("status").textContent=`LIVE · draft ${draftId} · API ${Math.max(0,Date.now()-lastApiAt)} ms ago · ${marketReady?marketSourceLabel:"ADP off"}`;''',
'''    $("status").textContent=`LIVE · ${draftProvider==="yahoo"?"Yahoo league":"Sleeper draft"} ${draftId} · API ${Math.max(0,Date.now()-lastApiAt)} ms ago · ${marketReady?marketSourceLabel:"ADP off"}`;''',
'provider live status'
)

rep(
'''          debugLogOnce(`name:${draftId}:${username}:${alias}`,"NAME",`${username} → ${alias} matched Sleeper slot ${slot} (${source})`);''',
'''          debugLogOnce(`name:${draftId}:${username}:${alias}`,"NAME",`${username} → ${alias} matched ${draftProvider==="yahoo"?"Yahoo":"Sleeper"} slot ${slot} (${source})`);''',
'name resolution log'
)
rep(
'''        debugLogOnce(`name-miss:${draftId}:${key}:${alias}`,"NAME?",`${key} → ${alias} has no matching Sleeper username in this draft`);''',
'''        debugLogOnce(`name-miss:${draftId}:${key}:${alias}`,"NAME?",`${key} → ${alias} has no matching manager identity in this ${draftProvider==="yahoo"?"Yahoo league":"Sleeper draft"}`);''',
'name miss log'
)

rep('The People tab controls broadcast names, Absent status and Auto-draft status per Sleeper username.',
    'The People tab controls broadcast names, Absent status and Auto-draft status per platform manager identity.',
    'settings identity note')
rep('<div id="board-title">Sleeper Draft Party</div>', '<div id="board-title">DraftCenter</div>', 'initial board title')
rep('<div class="people-help">Waiting for Sleeper users…</div>', '<div class="people-help">Waiting for platform managers…</div>', 'people waiting copy')

p.write_text(s,encoding='utf-8')
print('Hardened Yahoo OAuth refresh, provider switching, rounds, status and copy')
