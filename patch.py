from pathlib import Path

p=Path('index.html')
s=p.read_text(encoding='utf-8')

def rep(old,new,label):
    global s
    if old not in s:
        raise SystemExit(f'{label}: target not found')
    s=s.replace(old,new,1)

rep('if(t.access && (!t.expires || Date.now()<t.expires))return t.access;',
    'if(t.access && t.expires && Date.now()<t.expires)return t.access;',
    'yahoo access expiry')
rep('const data=await yahooTokenRequest({client_id:clientId,refresh_token:t.refresh,grant_type:"refresh_token"});',
    'const data=await yahooTokenRequest({client_id:clientId,redirect_uri:yahooCallbackUrl(),refresh_token:t.refresh,grant_type:"refresh_token"});',
    'yahoo refresh redirect')
rep('try{localStorage.setItem("draftcenterYahooExpiresAt","0")}catch(_){}',
    'try{localStorage.removeItem("draftcenterYahooAccessToken");localStorage.setItem("draftcenterYahooExpiresAt","0")}catch(_){}',
    'yahoo clear stale token')
rep('if(!r.ok)throw new Error(`Yahoo Fantasy API ${r.status}`);\n    return r.text();',
    'if(!r.ok)throw new Error(`Yahoo Fantasy API ${r.status}`);\n    lastApiAt=Date.now();\n    return r.text();',
    'yahoo api timestamp')
rep('const maxRound=raw.reduce((m,x)=>Math.max(m,x.round||0),0);\n    return Math.max(total,maxRound,15);',
    'const maxRound=raw.reduce((m,x)=>Math.max(m,x.round||0),0);\n    const resolved=Math.max(total,maxRound);\n    return resolved>0?resolved:15;',
    'yahoo rounds')
rep('if(Date.now()-yahooLastDraftPollAt<8000)return;',
    'if(Date.now()-yahooLastDraftPollAt<30000)return;',
    'yahoo draft throttle')
rep('''  $("draftProvider").addEventListener("change",e=>{\n    draftProvider=e.currentTarget.value==="yahoo"?"yahoo":"sleeper";\n    updateProviderUI();\n  });''',
'''  $("draftProvider").addEventListener("change",()=>{\n    // Editing the dropdown must not interrupt the currently running provider.\n    updateYahooAuthUI();\n  });''',
'provider selector safety')
rep('$("status").textContent=`LIVE · draft ${draftId} · API ${Math.max(0,Date.now()-lastApiAt)} ms ago · ${marketReady?marketSourceLabel:"ADP off"}`;',
    '$("status").textContent=`LIVE · ${draftProvider==="yahoo"?"Yahoo league":"Sleeper draft"} ${draftId} · API ${Math.max(0,Date.now()-lastApiAt)} ms ago · ${marketReady?marketSourceLabel:"ADP off"}`;',
    'provider live status')

# Provider-neutral wording. These are intentionally broad text swaps so minor indentation cannot break the patch.
s=s.replace('matched Sleeper slot ${slot}', 'matched ${draftProvider==="yahoo"?"Yahoo":"Sleeper"} slot ${slot}')
s=s.replace('has no matching Sleeper username in this draft', 'has no matching manager identity in this ${draftProvider==="yahoo"?"Yahoo league":"Sleeper draft"}')
s=s.replace('The People tab controls broadcast names, Absent status and Auto-draft status per Sleeper username.', 'The People tab controls broadcast names, Absent status and Auto-draft status per platform manager identity.')
s=s.replace('<div id="board-title">Sleeper Draft Party</div>', '<div id="board-title">DraftCenter</div>')
s=s.replace('<div class="people-help">Waiting for Sleeper users…</div>', '<div class="people-help">Waiting for platform managers…</div>')

p.write_text(s,encoding='utf-8')
print('Hardened Yahoo OAuth refresh, provider switching, rounds and status')
