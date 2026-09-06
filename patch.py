from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')


def rep(old, new, label):
    global s
    if old not in s:
        raise SystemExit(f'{label}: target not found')
    s = s.replace(old, new, 1)


def sub(pattern, repl, label, flags=re.S):
    global s
    s2, n = re.subn(pattern, repl, s, count=1, flags=flags)
    if n != 1:
        raise SystemExit(f'{label}: expected 1 replacement, got {n}')
    s = s2


rep('<title>Sleeper Draft Party TV</title>', '<title>DraftCenter Fantasy Draft TV</title>', 'title')

# Draft settings: add platform selection and device-local Yahoo OAuth controls.
rep(
'''  <section class="settings-pane active" id="draftPane">\n    <label>Sleeper Draft URL or Draft ID\n      <input id="draftInput" autocomplete="off">\n    </label>\n    <label>Admin GitHub token (this browser only)''',
'''  <section class="settings-pane active" id="draftPane">\n    <div class="settings-grid">\n      <label>Fantasy platform\n        <select id="draftProvider">\n          <option value="sleeper">Sleeper</option>\n          <option value="yahoo">Yahoo Fantasy</option>\n        </select>\n      </label>\n      <label id="yahooTimerRow" style="display:none">Yahoo pick timer (seconds)\n        <input id="yahooTimerInput" type="number" min="30" max="600" step="10" value="180">\n      </label>\n    </div>\n    <label id="draftInputLabel">Sleeper Draft URL or Draft ID\n      <input id="draftInput" autocomplete="off">\n    </label>\n    <div id="yahooAuthBox" style="display:none">\n      <label>Yahoo Client ID (this browser/device only)\n        <input id="yahooClientIdInput" autocomplete="off" placeholder="Yahoo OAuth Consumer Key / Client ID">\n      </label>\n      <div class="people-help">Yahoo leagues use OAuth. Create/approve a Yahoo Fantasy API application as a public client and register this exact callback URL: <strong id="yahooCallbackUrl"></strong>. The Client ID and Yahoo tokens stay only in this browser and are never written to the repo.</div>\n      <div class="settings-actions">\n        <button class="tool" id="connectYahoo" type="button">Connect Yahoo</button>\n        <button class="tool" id="disconnectYahoo" type="button">Disconnect Yahoo</button>\n      </div>\n      <div class="people-help" id="yahooAuthState">Yahoo not connected.</div>\n    </div>\n    <label>Admin GitHub token (this browser only)''',
'draft provider controls'
)

# Provider constants/state.
rep(
'''  const API = "https://api.sleeper.app/v1";\n  const PICKS_MS = 300;''',
'''  const API = "https://api.sleeper.app/v1";\n  const YAHOO_API = "https://fantasysports.yahooapis.com/fantasy/v2";\n  const YAHOO_AUTH_URL = "https://api.login.yahoo.com/oauth2/request_auth";\n  const YAHOO_TOKEN_URL = "https://api.login.yahoo.com/oauth2/get_token";\n  const PICKS_MS = 300;''',
'provider constants'
)

rep(
'''  let draftId = DEFAULT_DRAFT_ID;\n  let draft = null;''',
'''  let draftProvider = "sleeper";\n  let draftId = DEFAULT_DRAFT_ID;\n  let yahooLeagueKey = "";\n  let yahooPickTimer = 180;\n  let yahooTeamKeyToUid = {};\n  let yahooTeamKeyToSlot = {};\n  let yahooPlayerCache = {};\n  let yahooLastPicksPollAt = 0;\n  let yahooLastDraftPollAt = 0;\n  let yahooAdpBusy = false;\n  let draft = null;''',
'provider state'
)

# Shared-config summary should make the platform obvious.
rep(
'''    const text=`Shared config · draft ${draftId} · ${names} broadcast name${names===1?"":"s"} · ${absentUsernames.size} absent · ${autodraftUsernames.size} auto`;''',
'''    const text=`Shared config · ${draftProvider==="yahoo"?"Yahoo":"Sleeper"} · ${draftProvider==="yahoo"?"league":"draft"} ${draftId} · ${names} broadcast name${names===1?"":"s"} · ${absentUsernames.size} absent · ${autodraftUsernames.size} auto`;''',
'shared config summary'
)

# Yahoo does not use the secret-backed Muse worker yet; do not poll a mismatched feed.
rep(
'''  async function pollAIAnalysis(){\n    try{''',
'''  async function pollAIAnalysis(){\n    if(draftProvider==="yahoo"){\n      debugLogOnce(`ai-yahoo:${draftId}`,"AI",`Yahoo draft uses local deterministic analysis; Muse feed is disabled until the server worker has Yahoo OAuth.`);\n      return;\n    }\n    try{''',
'ai yahoo guard'
)

# Market labeling becomes provider-aware.
rep(
'''  function marketValue(p){\n    if(!marketReady)return null;\n    const rank=Number(sleeperAdpById[String(p?.player_id||"")]);\n    if(!Number.isFinite(rank) || rank<=0 || rank>=999)return null;\n    return {rank,label:"Sleeper ADP",source:adpScoringLabel()};\n  }''',
'''  function marketLabel(){ return draftProvider==="yahoo"?"Yahoo ADP":"Sleeper ADP"; }\n\n  function marketValue(p){\n    if(!marketReady)return null;\n    const rank=Number(sleeperAdpById[String(p?.player_id||"")]);\n    if(!Number.isFinite(rank) || rank<=0 || rank>=999)return null;\n    return {rank,label:marketLabel(),source:draftProvider==="yahoo"?"Yahoo draft analysis":adpScoringLabel()};\n  }''',
'market provider label'
)

# Insert Yahoo OAuth/API/normalization adapter before the generic player helpers.
rep(
'''  function pickName(p){\n    const m=p?.metadata||{};''',
'''  function yahooCallbackUrl(){\n    return `${location.origin}${location.pathname}`;\n  }\n\n  function yahooClientId(){\n    try{return localStorage.getItem("draftcenterYahooClientId")||""}catch(_){return ""}\n  }\n\n  function rememberYahooClientId(v){\n    try{\n      if(v)localStorage.setItem("draftcenterYahooClientId",v);\n      else localStorage.removeItem("draftcenterYahooClientId");\n    }catch(_){}\n  }\n\n  function yahooTokenState(){\n    try{\n      return {\n        access:localStorage.getItem("draftcenterYahooAccessToken")||"",\n        refresh:localStorage.getItem("draftcenterYahooRefreshToken")||"",\n        expires:Number(localStorage.getItem("draftcenterYahooExpiresAt")||0)\n      };\n    }catch(_){return {access:"",refresh:"",expires:0}}\n  }\n\n  function saveYahooTokens(data){\n    try{\n      const now=Date.now();\n      if(data?.access_token)localStorage.setItem("draftcenterYahooAccessToken",String(data.access_token));\n      if(data?.refresh_token)localStorage.setItem("draftcenterYahooRefreshToken",String(data.refresh_token));\n      if(data?.expires_in)localStorage.setItem("draftcenterYahooExpiresAt",String(now+Math.max(60,Number(data.expires_in)-60)*1000));\n    }catch(_){}\n    updateYahooAuthUI();\n  }\n\n  function clearYahooTokens(){\n    try{\n      ["draftcenterYahooAccessToken","draftcenterYahooRefreshToken","draftcenterYahooExpiresAt"].forEach(k=>localStorage.removeItem(k));\n    }catch(_){}\n    updateYahooAuthUI();\n  }\n\n  function b64url(bytes){\n    let s="";for(const b of bytes)s+=String.fromCharCode(b);\n    return btoa(s).replace(/\\+/g,"-").replace(/\\//g,"_").replace(/=+$/g,"");\n  }\n\n  async function sha256url(text){\n    const bytes=new TextEncoder().encode(text);\n    return b64url(new Uint8Array(await crypto.subtle.digest("SHA-256",bytes)));\n  }\n\n  async function startYahooAuth(){\n    const clientId=String($("yahooClientIdInput")?.value||yahooClientId()).trim();\n    if(!clientId){$("yahooAuthState").textContent="Enter your Yahoo Client ID first.";return;}\n    rememberYahooClientId(clientId);\n    const verifier=b64url(crypto.getRandomValues(new Uint8Array(48)));\n    const challenge=await sha256url(verifier);\n    const state=b64url(crypto.getRandomValues(new Uint8Array(24)));\n    try{\n      sessionStorage.setItem("draftcenterYahooPkceVerifier",verifier);\n      sessionStorage.setItem("draftcenterYahooOauthState",state);\n    }catch(_){}\n    const u=new URL(YAHOO_AUTH_URL);\n    u.searchParams.set("client_id",clientId);\n    u.searchParams.set("redirect_uri",yahooCallbackUrl());\n    u.searchParams.set("response_type","code");\n    u.searchParams.set("code_challenge",challenge);\n    u.searchParams.set("code_challenge_method","S256");\n    u.searchParams.set("state",state);\n    location.assign(u.toString());\n  }\n\n  async function yahooTokenRequest(params){\n    const body=new URLSearchParams(params);\n    const r=await fetch(YAHOO_TOKEN_URL,{\n      method:"POST",\n      headers:{"Content-Type":"application/x-www-form-urlencoded","Accept":"application/json"},\n      body,cache:"no-store",credentials:"omit"\n    });\n    const data=await r.json().catch(()=>({}));\n    if(!r.ok)throw new Error(data?.error_description||data?.error||`Yahoo token HTTP ${r.status}`);\n    saveYahooTokens(data);\n    return data;\n  }\n\n  async function processYahooOAuthCallback(){\n    const q=new URLSearchParams(location.search);\n    const code=q.get("code");\n    if(!code)return false;\n    const returnedState=q.get("state")||"";\n    let expected="",verifier="";\n    try{expected=sessionStorage.getItem("draftcenterYahooOauthState")||"";verifier=sessionStorage.getItem("draftcenterYahooPkceVerifier")||""}catch(_){}\n    if(expected && returnedState!==expected)throw new Error("Yahoo OAuth state did not match.");\n    const clientId=yahooClientId();\n    if(!clientId||!verifier)throw new Error("Yahoo OAuth callback is missing its local PKCE session. Connect Yahoo again.");\n    await yahooTokenRequest({client_id:clientId,redirect_uri:yahooCallbackUrl(),code,grant_type:"authorization_code",code_verifier:verifier});\n    try{sessionStorage.removeItem("draftcenterYahooOauthState");sessionStorage.removeItem("draftcenterYahooPkceVerifier")}catch(_){}\n    history.replaceState({},document.title,`${location.pathname}${location.hash||""}`);\n    debugLog("YAHOO","OAuth connected successfully");\n    return true;\n  }\n\n  async function ensureYahooToken(){\n    const t=yahooTokenState();\n    if(t.access && (!t.expires || Date.now()<t.expires))return t.access;\n    if(t.refresh){\n      const clientId=yahooClientId();\n      if(!clientId)throw new Error("Yahoo Client ID missing on this device.");\n      const data=await yahooTokenRequest({client_id:clientId,refresh_token:t.refresh,grant_type:"refresh_token"});\n      return String(data.access_token||"");\n    }\n    throw new Error("Yahoo is not connected on this device. Open Settings → Draft → Connect Yahoo.");\n  }\n\n  async function yahooApiText(path,retry=true){\n    const token=await ensureYahooToken();\n    const sep=path.includes("?")?"&":"?";\n    const r=await fetch(`${YAHOO_API}${path}${sep}_dc=${Date.now()}`,{\n      cache:"no-store",credentials:"omit",\n      headers:{"Authorization":`Bearer ${token}`,"Accept":"application/xml,text/xml;q=0.9,*/*;q=0.8"}\n    });\n    if(r.status===401 && retry){\n      try{localStorage.setItem("draftcenterYahooExpiresAt","0")}catch(_){}\n      return yahooApiText(path,false);\n    }\n    if(!r.ok)throw new Error(`Yahoo Fantasy API ${r.status}`);\n    return r.text();\n  }\n\n  function yahooXml(text){\n    const doc=new DOMParser().parseFromString(text,"application/xml");\n    if(doc.getElementsByTagName("parsererror").length)throw new Error("Yahoo returned invalid XML");\n    return doc;\n  }\n\n  function yText(node,name){\n    const el=node?.getElementsByTagName(name)?.[0];\n    return String(el?.textContent||"").trim();\n  }\n\n  function yDirect(node,name){\n    if(!node)return "";\n    const el=[...node.children].find(x=>x.localName===name);\n    return String(el?.textContent||"").trim();\n  }\n\n  function parseYahooLeagueKey(v){\n    const raw=String(v||"").trim();\n    const exact=raw.match(/((?:nfl|\\d+)\\.l\\.\\d+)/i);\n    if(exact)return exact[1].toLowerCase();\n    const f1=raw.match(/(?:football\\.)?fantasysports\\.yahoo\\.com\\/(?:[^/]+\\/)?f1\\/(\\d+)/i);\n    if(f1)return `nfl.l.${f1[1]}`;\n    const id=raw.match(/(?:league_id|lid)[=/](\\d+)/i)||raw.match(/^\\d+$/);\n    if(id)return `nfl.l.${id[1]||id[0]}`;\n    return "";\n  }\n\n  function parseYahooTeams(doc){\n    return [...doc.getElementsByTagName("team")].map((team,i)=>{\n      const teamKey=yDirect(team,"team_key")||yText(team,"team_key");\n      if(!teamKey)return null;\n      const teamId=Number(yDirect(team,"team_id")||yText(team,"team_id")||i+1);\n      const teamName=yDirect(team,"name")||`Team ${teamId}`;\n      const slot=Number(yDirect(team,"draft_position")||yText(team,"draft_position")||teamId);\n      const manager=team.getElementsByTagName("manager")?.[0];\n      const managerName=yDirect(manager,"nickname")||yDirect(manager,"email")||yDirect(manager,"manager_id")||teamName;\n      const managerId=yDirect(manager,"guid")||yDirect(manager,"manager_id")||teamKey;\n      const logoNode=team.getElementsByTagName("team_logo")?.[0];\n      const logo=yText(logoNode,"url")||"";\n      return {teamKey,teamId,teamName,slot,managerName,managerId,logo};\n    }).filter(Boolean).sort((a,b)=>a.slot-b.slot);\n  }\n\n  function installYahooTeams(teams){\n    const order={};\n    const nextUsers={},nextLeagueUsers={};\n    yahooTeamKeyToUid={};\n    yahooTeamKeyToSlot={};\n    for(const t of teams){\n      const uid=`yahoo:${t.teamKey}`;\n      yahooTeamKeyToUid[t.teamKey]=uid;\n      yahooTeamKeyToSlot[t.teamKey]=t.slot;\n      order[uid]=t.slot;\n      nextUsers[uid]={user_id:uid,username:String(t.managerName||t.teamName),display_name:String(t.managerName||t.teamName),avatar:t.logo||null};\n      nextLeagueUsers[uid]={user_id:uid,username:String(t.managerName||t.teamName),display_name:String(t.managerName||t.teamName),avatar:t.logo||null,metadata:{team_name:t.teamName}};\n    }\n    users=nextUsers;leagueUsers=nextLeagueUsers;\n    return order;\n  }\n\n  function parseYahooDraftResults(doc){\n    return [...doc.getElementsByTagName("draft_result")].map(x=>({\n      pick:Number(yDirect(x,"pick")||yText(x,"pick")||0),\n      round:Number(yDirect(x,"round")||yText(x,"round")||0),\n      teamKey:yDirect(x,"team_key")||yText(x,"team_key"),\n      playerKey:yDirect(x,"player_key")||yText(x,"player_key")\n    })).filter(x=>x.pick>0&&x.round>0&&x.teamKey&&x.playerKey).sort((a,b)=>a.pick-b.pick);\n  }\n\n  function parseYahooPlayerElement(player){\n    const key=yDirect(player,"player_key")||yText(player,"player_key");\n    if(!key)return null;\n    const nameNode=player.getElementsByTagName("name")?.[0];\n    const full=yText(nameNode,"full")||key;\n    const first=yText(nameNode,"first")||full.split(/\\s+/)[0]||"";\n    const last=yText(nameNode,"last")||full.split(/\\s+/).slice(1).join(" ");\n    const pos=yDirect(player,"display_position")||yDirect(player,"primary_position")||yText(player,"display_position")||yText(player,"primary_position")||"";\n    const team=yDirect(player,"editorial_team_abbr")||yText(player,"editorial_team_abbr")||"FA";\n    const headshot=player.getElementsByTagName("headshot")?.[0];\n    const image=yText(headshot,"url")||"";\n    const da=player.getElementsByTagName("draft_analysis")?.[0];\n    const adp=Number(yText(da,"average_pick")||0);\n    return {key,full,first,last,pos,team,image,adp:Number.isFinite(adp)&&adp>0?adp:null};\n  }\n\n  function installYahooPlayers(doc){\n    for(const p of [...doc.getElementsByTagName("player")]){\n      const x=parseYahooPlayerElement(p);\n      if(x)yahooPlayerCache[x.key]=x;\n    }\n  }\n\n  async function yahooEnsurePlayers(keys){\n    const missing=[...new Set(keys.filter(Boolean))].filter(k=>!yahooPlayerCache[k]);\n    for(let i=0;i<missing.length;i+=25){\n      const batch=missing.slice(i,i+25);\n      const xml=await yahooApiText(`/players;player_keys=${batch.map(encodeURIComponent).join(",")};out=draft_analysis`);\n      installYahooPlayers(yahooXml(xml));\n    }\n  }\n\n  function normalizeYahooPicks(raw){\n    return raw.map(x=>{\n      const pl=yahooPlayerCache[x.playerKey]||{full:x.playerKey,first:"",last:"",pos:"",team:"FA",image:""};\n      return {\n        pick_no:x.pick,round:x.round,draft_slot:Number(yahooTeamKeyToSlot[x.teamKey]||0),\n        picked_by:yahooTeamKeyToUid[x.teamKey]||`yahoo:${x.teamKey}`,\n        player_id:x.playerKey,is_keeper:false,\n        metadata:{first_name:pl.first,last_name:pl.last,full_name:pl.full,position:pl.pos,team:pl.team,image_url:pl.image,provider:"yahoo"}\n      };\n    }).filter(p=>p.draft_slot>0);\n  }\n\n  function yahooRoundsFromSettings(doc,raw){\n    let total=0;\n    for(const rp of [...doc.getElementsByTagName("roster_position")]){\n      const pos=(yDirect(rp,"position")||yText(rp,"position")).toUpperCase();\n      const count=Number(yDirect(rp,"count")||yText(rp,"count")||0);\n      if(!["IR","IL","NA"].includes(pos))total+=Math.max(0,count);\n    }\n    const maxRound=raw.reduce((m,x)=>Math.max(m,x.round||0),0);\n    return Math.max(total,maxRound,15);\n  }\n\n  function normalizeYahooDraft(metaDoc,settingsDoc,teams,raw,order,key){\n    const league=metaDoc.getElementsByTagName("league")?.[0];\n    const name=yDirect(league,"name")||`Yahoo League ${key}`;\n    const numTeams=Number(yDirect(league,"num_teams")||teams.length||10);\n    const rawStatus=(yDirect(league,"draft_status")||"").toLowerCase();\n    const settings=settingsDoc.getElementsByTagName("settings")?.[0]||settingsDoc.documentElement;\n    const draftType=(yText(settings,"draft_type")||"standard").toLowerCase();\n    if(/auction|salary/.test(draftType))throw new Error("Yahoo auction/salary-cap drafts are not supported by this DraftCenter board yet.");\n    const rounds=yahooRoundsFromSettings(settingsDoc,raw);\n    const total=numTeams*rounds;\n    let status="pre_draft";\n    if(/post|complete/.test(rawStatus)||raw.length>=total)status="complete";\n    else if(raw.length>0||/drafting|inprogress|in_progress/.test(rawStatus))status="drafting";\n    const scoring=yText(settings,"scoring_type")||"yahoo";\n    return {\n      draft_id:key,league_id:key,type:"snake",status,season:new Date().getFullYear(),draft_order:order,\n      settings:{teams:numTeams,rounds,pick_timer:yahooPickTimer,reversal_round:0},\n      metadata:{name,scoring_type:scoring,provider:"yahoo",draft_status:rawStatus},\n      start_time:Date.now(),last_picked:Number(observedPickAt||0)\n    };\n  }\n\n  async function fetchYahooSnapshot(key){\n    const enc=encodeURIComponent(key);\n    const [metaText,settingsText,teamsText,draftText]=await Promise.all([\n      yahooApiText(`/league/${enc}`),\n      yahooApiText(`/league/${enc}/settings`),\n      yahooApiText(`/league/${enc}/teams`),\n      yahooApiText(`/league/${enc}/draftresults`).catch(e=>{if(String(e.message).includes("404"))return "<fantasy_content/>";throw e;})\n    ]);\n    const metaDoc=yahooXml(metaText),settingsDoc=yahooXml(settingsText),teamsDoc=yahooXml(teamsText),draftDoc=yahooXml(draftText);\n    const teams=parseYahooTeams(teamsDoc);\n    if(!teams.length)throw new Error("Yahoo returned no fantasy teams for that league.");\n    const order=installYahooTeams(teams);\n    const raw=parseYahooDraftResults(draftDoc);\n    await yahooEnsurePlayers(raw.map(x=>x.playerKey));\n    const nextDraft=normalizeYahooDraft(metaDoc,settingsDoc,teams,raw,order,key);\n    const nextPicks=normalizeYahooPicks(raw);\n    return {draft:nextDraft,picks:nextPicks};\n  }\n\n  async function pollYahooDraft(){\n    if(Date.now()-yahooLastDraftPollAt<8000)return;\n    yahooLastDraftPollAt=Date.now();\n    try{\n      const key=yahooLeagueKey||draftId;\n      if(!key)return;\n      const snap=await fetchYahooSnapshot(key);\n      const first=!draft;\n      draft=snap.draft;\n      if(first){picks=snap.picks;lastPickCount=picks.length;turnStartedAt=Date.now();debugLog("YAHOO",`loaded ${key} · ${draft.settings.teams} teams · ${draft.settings.rounds} rounds · ${picks.length} picks`);}\n      renderAll();logNameResolution("Yahoo");\n      if(first)loadSleeperADP();\n    }catch(e){\n      $("status").textContent=e.message;$("status").classList.add("bad");\n      debugLogOnce(`yahoo-draft:${draftId}:${e.message}`,"YAHOO!",e.message);\n      updateYahooAuthUI();\n    }\n  }\n\n  async function pollYahooPicks(){\n    if(Date.now()-yahooLastPicksPollAt<2000)return;\n    if(picksBusy)return;\n    yahooLastPicksPollAt=Date.now();picksBusy=true;\n    try{\n      const key=yahooLeagueKey||draftId;\n      const text=await yahooApiText(`/league/${encodeURIComponent(key)}/draftresults`).catch(e=>{if(String(e.message).includes("404"))return "<fantasy_content/>";throw e;});\n      const raw=parseYahooDraftResults(yahooXml(text));\n      await yahooEnsurePlayers(raw.map(x=>x.playerKey));\n      const next=normalizeYahooPicks(raw);\n      processPickSnapshot(next);\n      if(draft){\n        const total=Number(draft.settings?.teams||10)*Number(draft.settings?.rounds||15);\n        if(next.length>=total)draft.status="complete";else if(next.length>0)draft.status="drafting";\n      }\n    }catch(e){$("status").textContent=e.message;$("status").classList.add("bad");}\n    finally{picksBusy=false;}\n  }\n\n  async function loadYahooADP(){\n    if(yahooAdpBusy||!draft||draftProvider!=="yahoo")return;\n    const attemptKey=`yahoo:${yahooLeagueKey||draftId}`;\n    if(adpAttemptedFor===attemptKey)return;\n    adpAttemptedFor=attemptKey;yahooAdpBusy=true;\n    try{\n      const rowsById={};\n      const addCached=()=>{\n        for(const pl of Object.values(yahooPlayerCache)){\n          if(!pl?.adp)continue;\n          rowsById[pl.key]={player_id:pl.key,adp:Number(pl.adp),full_name:pl.full,fantasy_positions:[pl.pos],team:pl.team};\n        }\n      };\n      addCached();\n      const key=yahooLeagueKey||draftId;\n      for(let start=0;start<150;start+=25){\n        const xml=await yahooApiText(`/league/${encodeURIComponent(key)}/players;status=A;sort=OR;start=${start};count=25;out=draft_analysis`);\n        const doc=yahooXml(xml);\n        const found=[...doc.getElementsByTagName("player")];\n        installYahooPlayers(doc);addCached();\n        if(found.length<25)break;\n      }\n      const rows=Object.values(rowsById).filter(x=>Number.isFinite(x.adp)&&x.adp>0&&x.adp<999).sort((a,b)=>a.adp-b.adp);\n      adpRows=rows;sleeperAdpById=Object.fromEntries(rows.map(x=>[x.player_id,x.adp]));\n      marketReady=rows.length>0;marketSourceLabel=marketReady?"Yahoo ADP":"Yahoo ADP unavailable";\n      debugLog("YAHOO",`Yahoo ADP loaded · ${rows.length} players`);\n      renderAll();\n    }catch(e){\n      marketReady=false;adpRows=[];sleeperAdpById={};marketSourceLabel="Yahoo ADP unavailable";\n      debugLog("YAHOO!",`Yahoo ADP unavailable: ${e.message}`);\n    }finally{yahooAdpBusy=false;}\n  }\n\n  function updateYahooAuthUI(){\n    const box=$("yahooAuthBox"),timerRow=$("yahooTimerRow");\n    const yahoo=draftProvider==="yahoo" || $("draftProvider")?.value==="yahoo";\n    if(box)box.style.display=yahoo?"block":"none";\n    if(timerRow)timerRow.style.display=yahoo?"block":"none";\n    const label=$("draftInputLabel");\n    if(label)label.childNodes[0].nodeValue=yahoo?"Yahoo League URL / League Key / League ID\\n      ":"Sleeper Draft URL or Draft ID\\n      ";\n    const cbEl=$("yahooCallbackUrl");if(cbEl)cbEl.textContent=yahooCallbackUrl();\n    const cid=$("yahooClientIdInput");if(cid && !cid.value)cid.value=yahooClientId();\n    const st=$("yahooAuthState");if(st){\n      const t=yahooTokenState();\n      st.textContent=t.access?"Yahoo connected on this device.":(t.refresh?"Yahoo refresh token available; connection will renew automatically.":"Yahoo not connected on this device.");\n    }\n  }\n\n  function updateProviderUI(){\n    const sel=$("draftProvider");if(sel)sel.value=draftProvider;\n    if($("yahooTimerInput"))$("yahooTimerInput").value=yahooPickTimer;\n    if($("draftInput")){\n      $("draftInput").value=draftProvider==="yahoo"?(yahooLeagueKey||draftId):`https://sleeper.com/draft/nfl/${draftId}`;\n    }\n    updateYahooAuthUI();\n  }\n\n  function pickName(p){\n    const m=p?.metadata||{};''',
'yahoo adapter block'
)

# Full URLs from Yahoo should pass through untouched for avatars/headshots.
rep(
'''  function playerImg(p){ return p?.player_id ? `https://sleepercdn.com/content/nfl/players/${encodeURIComponent(p.player_id)}.jpg` : ""; }\n  function avatarImg(a,thumb=false){ return a ? `https://sleepercdn.com/avatars/${thumb?"thumbs/":""}${encodeURIComponent(a)}` : ""; }''',
'''  function playerImg(p){\n    const direct=String(p?.metadata?.image_url||"");\n    if(direct)return direct;\n    return p?.player_id ? `https://sleepercdn.com/content/nfl/players/${encodeURIComponent(p.player_id)}.jpg` : "";\n  }\n  function avatarImg(a,thumb=false){\n    if(!a)return "";\n    if(/^https?:\\/\\//i.test(String(a)))return String(a);\n    return `https://sleepercdn.com/avatars/${thumb?"thumbs/":""}${encodeURIComponent(a)}`;\n  }''',
'yahoo image URLs'
)

# Yahoo teams are already hydrated by the adapter.
rep(
'''  async function hydrate(){\n    if(!draft)return;''',
'''  async function hydrate(){\n    if(!draft)return;\n    if(draftProvider==="yahoo"){renderAll();logNameResolution("Yahoo");if($("settings")?.classList.contains("open"))renderPeopleSettings();return;}''',
'yahoo hydrate'
)

# Provider-aware polling.
rep(
'''  async function pollDraft(){\n    if(draftNotFound)return;''',
'''  async function pollDraft(){\n    if(draftProvider==="yahoo")return pollYahooDraft();\n    if(draftNotFound)return;''',
'yahoo draft polling branch'
)

# Refactor the pick snapshot processing so Sleeper and Yahoo share ALL broadcasts/roasts/events.
sub(
    r'''  async function pollPicks\(\)\{[\s\S]*?\n  \}\n\n\n  function runBroadcastDemo\(\)\{''',
'''  function processPickSnapshot(next){\n    const previousLiveKeys=new Set(picks.filter(p=>!isKeeperPick(p)).map(p=>pickCellKey(p)));\n    const incomingLive=next\n      .filter(p=>!isKeeperPick(p))\n      .filter(p=>!previousLiveKeys.has(pickCellKey(p)));\n\n    if(lastPickCount!==null && incomingLive.length){\n      const now=Date.now();\n      const secondsOnClock=Math.max(0,(now-turnStartedAt)/1000);\n      if(activeEvent && activeEvent.kind==="followup")rememberDeferred(activeEvent);\n      for(const pending of eventQueue){if(pending?.kind==="followup")rememberDeferred(pending);}\n      hidePressure();playPickStinger();stopAudioGroup("warning");warningCrowdStarted=false;\n      activeEvent=null;activeUntil=0;eventQueue.length=0;\n      observedPickAt=now;lastLivePickAt=now;picks=next;insightIndex=0;\n      incomingLive.sort((a,b)=>{\n        const ca=cellForPick(a)?.ordinal||Number(a.pick_no||0);\n        const cb=cellForPick(b)?.ordinal||Number(b.pick_no||0);\n        return ca-cb;\n      }).forEach(p=>{\n        const cell=cellForPick(p);lastLivePickKey=pickCellKey(p);\n        const pickOwner=ownerForPick(p);const mgr=broadcastName(pickOwner);const mv=marketValue(p);\n        const ordinal=Number(cell?.ordinal||p.pick_no||0);const delta=mv?ordinal-Number(mv.rank):null;\n        debugLog("PICK",`${cell?.label||formatCellLabel(p)} · ${pickName(p)} (${p?.metadata?.position||"—"}) · ${mgr}${managerUsername(pickOwner)?` @${managerUsername(pickOwner)}`:""}${mv?` · ${mv.label} ${mv.rank.toFixed(1)} · ${delta>=0?"+":""}${Math.round(delta)}`:""}${isAutodraftManager(pickOwner)?" · AUTO-MARKED":""}`);\n        observedPickTimes.push({pick:Number(cell?.ordinal||p.pick_no||0),seconds:secondsOnClock,manager:mgr});\n        observedPickTimes=observedPickTimes.slice(-80);queueEventsForPick(p,secondsOnClock);\n      });\n      turnStartedAt=now;\n    }else{picks=next;}\n    lastPickCount=next.length;renderAll();\n  }\n\n  async function pollPicks(){\n    if(draftProvider==="yahoo")return pollYahooPicks();\n    if(draftNotFound)return;\n    if(picksBusy)return;picksBusy=true;\n    try{\n      const arr=await apiGet(`/draft/${draftId}/picks`);\n      const next=Array.isArray(arr)?arr.slice().sort((a,b)=>Number(a.pick_no)-Number(b.pick_no)):[];\n      processPickSnapshot(next);\n    }catch(e){$("status").textContent=`Picks API error: ${e.message}`;$("status").classList.add("bad");}\n    finally{picksBusy=false;}\n  }\n\n\n  function runBroadcastDemo(){''',
    'shared pick snapshot processing'
)

# Yahoo gets Yahoo ADP; Sleeper retains scoring-format ADP.
rep(
'''  async function loadSleeperADP(){\n    if(!draft)return;''',
'''  async function loadSleeperADP(){\n    if(draftProvider==="yahoo")return loadYahooADP();\n    if(!draft)return;''',
'yahoo adp branch'
)

# Dynamic market label in best-available bar.
rep(
'''      $("market-watch").innerHTML=`BEST AVAILABLE · <strong>${esc(ba.full_name||"—")}</strong> · Sleeper ADP ${Number(ba.adp).toFixed(1)}${slide>=8?` · ${Math.round(slide)} picks past ADP`:""}`;''',
'''      $("market-watch").innerHTML=`BEST AVAILABLE · <strong>${esc(ba.full_name||"—")}</strong> · ${esc(marketLabel())} ${Number(ba.adp).toFixed(1)}${slide>=8?` · ${Math.round(slide)} picks past ADP`:""}`;''',
'best available market label'
)

# Yahoo attribution is required when Yahoo data is displayed.
rep(
'''    $("api-state").innerHTML=`<span class="dot"></span><span>${draft.status==="drafting"?"Draft live":String(draft.status||"Synced")}</span>`;''',
'''    $("api-state").innerHTML=`<span class="dot"></span><span>${draft.status==="drafting"?"Draft live":String(draft.status||"Synced")}</span>${draftProvider==="yahoo"?`<span> · <a href="https://football.fantasysports.yahoo.com/" target="_blank" rel="noopener" style="color:inherit">Fantasy data provided by Yahoo Fantasy</a></span>`:""}`;''',
'yahoo attribution'
)

# Rename the existing Sleeper loader, add a provider-dispatch wrapper and Yahoo loader.
rep('  async function loadDraft(v){', '  async function loadSleeperDraft(v){', 'rename sleeper loader')

rep(
'''  async function loadSleeperDraft(v){\n    const m=String(v||"").match(/(\\d{10,})/);''',
'''  async function loadDraft(v){\n    const raw=String(v||"").trim();\n    let provider=$("draftProvider")?.value||draftProvider;\n    if(/yahoo/i.test(raw)||/(?:nfl|\\d+)\\.l\\.\\d+/i.test(raw))provider="yahoo";\n    if(provider==="yahoo")return loadYahooLeague(raw);\n    return loadSleeperDraft(raw);\n  }\n\n  async function loadYahooLeague(v){\n    const key=parseYahooLeagueKey(v);\n    if(!key){$("status").textContent="Enter a valid Yahoo Fantasy Football league URL, league key, or league ID.";$("status").classList.add("bad");return;}\n    const timer=Math.max(30,Math.min(600,Number($("yahooTimerInput")?.value||yahooPickTimer||180)));\n    yahooPickTimer=timer;\n    $("status").classList.remove("bad");$("status").textContent=`Checking Yahoo league ${key}…`;\n    let snap;\n    try{snap=await fetchYahooSnapshot(key)}catch(e){\n      $("status").textContent=e.message;$("status").classList.add("bad");debugLog("YAHOO!",e.message);updateYahooAuthUI();return;\n    }\n    const changed=draftProvider!=="yahoo"||String(yahooLeagueKey||draftId)!==String(key);\n    draftProvider="yahoo";yahooLeagueKey=key;draftId=key;\n    if(changed){broadcastNames={};absentUsernames=new Set();autodraftUsernames=new Set();roastDecks.clear();}\n    roastLevel=$("roastLevel").value;\n    const saved=await saveSharedSettings({reload:false});if(!saved)return;\n    stopAudioGroup("warning");hidePressure();draft=snap.draft;picks=snap.picks;lastPickCount=picks.length;\n    observedPickAt=null;const initialLive=picks.filter(p=>!isKeeperPick(p));lastLivePickKey=initialLive.length?pickCellKey(initialLive[initialLive.length-1]):"";\n    currentLiveOrdinal=1;marketReady=false;adpRows=[];sleeperAdpById={};adpAttemptedFor="";aiAnalysis=null;lastAiRevision="";\n    turnStartedAt=Date.now();warningCrowdStarted=false;draftNotFound=false;\n    updateProviderUI();$("settings").classList.remove("open");\n    debugLog("YAHOO",`validated and switched to ${key} · ${draft.settings.teams} teams · ${picks.length} picks`);\n    renderAll();logNameResolution("Yahoo");loadSleeperADP();pollYahooPicks();\n  }\n\n  async function loadSleeperDraft(v){\n    const m=String(v||"").match(/(\\d{10,})/);''',
'provider load wrapper'
)

# Ensure saving a Sleeper draft switches provider back to Sleeper.
rep(
'''    const draftChanged=nextDraftId!==draftId;\n    draftId=nextDraftId;''',
'''    const draftChanged=draftProvider!=="sleeper"||nextDraftId!==draftId;\n    draftProvider="sleeper";\n    yahooLeagueKey="";\n    draftId=nextDraftId;''',
'sleeper provider switch'
)

# Shared config now persists provider/ref and Yahoo timer, without any Yahoo credentials/tokens.
sub(
    r'''  function applySharedSettings\(cfg\)\{[\s\S]*?\n  \}\n\n  function adminToken\(\)\{''',
'''  function applySharedSettings(cfg){\n    if(!cfg||typeof cfg!=="object")return;\n    draftProvider=cfg.provider==="yahoo"?"yahoo":"sleeper";\n    yahooPickTimer=Math.max(30,Math.min(600,Number(cfg.yahooPickTimer||180)));\n    if(draftProvider==="yahoo"){\n      const key=parseYahooLeagueKey(cfg.yahooLeagueKey||cfg.draftId||"");\n      if(key){yahooLeagueKey=key;draftId=key;}\n    }else{\n      const id=String(cfg.draftId||"").replace(/\\D/g,"");\n      if(id)draftId=id;\n      yahooLeagueKey="";\n    }\n    absentUsernames=new Set((Array.isArray(cfg.absent)?cfg.absent:[]).map(x=>String(x).trim().toLowerCase()).filter(Boolean));\n    autodraftUsernames=new Set((Array.isArray(cfg.autodraft)?cfg.autodraft:[]).map(x=>String(x).trim().toLowerCase()).filter(Boolean));\n    broadcastNames=Object.fromEntries(Object.entries((cfg.broadcastNames&&typeof cfg.broadcastNames==="object")?cfg.broadcastNames:{})\n      .map(([k,v])=>[String(k).trim().toLowerCase(),String(v||"").trim()]).filter(([k,v])=>k&&v));\n    roastLevel=["off","light","spicy"].includes(cfg.roastLevel)?cfg.roastLevel:"spicy";\n  }\n\n  function adminToken(){''',
    'provider shared config load'
)

sub(
    r'''  function sharedPayload\(\)\{\n    return \{[\s\S]*?\n    \};\n  \}''',
'''  function sharedPayload(){\n    return {\n      provider:draftProvider,\n      draftId,\n      yahooLeagueKey:draftProvider==="yahoo"?(yahooLeagueKey||draftId):"",\n      yahooPickTimer:draftProvider==="yahoo"?yahooPickTimer:undefined,\n      roastLevel,\n      broadcastNames,\n      absent:[...absentUsernames],\n      autodraft:[...autodraftUsernames]\n    };\n  }''',
    'provider shared payload'
)

# Settings population and controls.
rep(
'''  function populateLeagueSettings(){\n    $("draftInput").value=`https://sleeper.com/draft/nfl/${draftId}`;\n    $("adminTokenInput").value=adminToken();''',
'''  function populateLeagueSettings(){\n    updateProviderUI();\n    $("adminTokenInput").value=adminToken();''',
'populate provider settings'
)

rep(
'''  $("positionPalette").addEventListener("change",e=>{''',
'''  $("draftProvider").addEventListener("change",e=>{\n    draftProvider=e.currentTarget.value==="yahoo"?"yahoo":"sleeper";\n    updateProviderUI();\n  });\n  $("yahooTimerInput").addEventListener("change",e=>{yahooPickTimer=Math.max(30,Math.min(600,Number(e.currentTarget.value)||180));e.currentTarget.value=yahooPickTimer;});\n  $("connectYahoo").addEventListener("click",startYahooAuth);\n  $("disconnectYahoo").addEventListener("click",()=>{clearYahooTokens();debugLog("YAHOO","Yahoo disconnected on this device")});\n\n  $("positionPalette").addEventListener("change",e=>{''',
'provider settings listeners'
)

# Boot handles Yahoo OAuth callback before reading shared provider config.
rep(
'''  async function boot(){\n    loadPositionPalette();\n    // Shared league settings are loaded once per page load.''',
'''  async function boot(){\n    loadPositionPalette();\n    try{await processYahooOAuthCallback()}catch(e){debugLog("YAHOO!",e.message);$("status").textContent=e.message;$("status").classList.add("bad");}\n    // Shared league settings are loaded once per page load.''',
'yahoo oauth boot callback'
)

rep(
'''    await loadSharedSettings();\n    debugLog("BOOT",`DraftCenter session started for ${draftId}`);\n    $("draftInput").value=`https://sleeper.com/draft/nfl/${draftId}`;\n    $("status").textContent=`Connecting to Sleeper draft ${draftId}…`;''',
'''    await loadSharedSettings();\n    updateProviderUI();\n    debugLog("BOOT",`DraftCenter session started for ${draftProvider} ${draftId}`);\n    $("status").textContent=draftProvider==="yahoo"?`Connecting to Yahoo league ${draftId}…`:`Connecting to Sleeper draft ${draftId}…`;''',
'provider boot status'
)

# Startup watchdog wording should be provider-neutral.
rep(
'''      const msg=`Still waiting for Sleeper draft ${draftId}. Open Settings → Debug for the exact startup error.`;''',
'''      const msg=`Still waiting for ${draftProvider==="yahoo"?"Yahoo league":"Sleeper draft"} ${draftId}. Open Settings → Debug for the exact startup error.`;''',
'provider watchdog'
)

# People copy and settings note become platform-neutral.
rep('Sleeper identities load automatically. Broadcast name is what DraftCenter says in announcements; the board keeps Sleeper\'s original identity.',
    'Manager identities load automatically from the selected fantasy platform. Broadcast name is what DraftCenter says in announcements; the board keeps the platform identity.',
    'people provider copy')
rep('DraftCenter follows one saved Sleeper draft configured in the Draft tab.',
    'DraftCenter follows one saved Sleeper draft or Yahoo league configured in the Draft tab.',
    'settings provider note')

p.write_text(s, encoding='utf-8')
print('Added integrated Yahoo Fantasy OAuth, league/draft adapter, shared broadcasts, and Yahoo ADP support')
