from pathlib import Path

path = Path("index.html")
s = path.read_text(encoding="utf-8")

old = '''    <label>Sleeper Draft URL or Draft ID
      <input id="draftInput" autocomplete="off">
    </label>
    <div class="people-help">DraftCenter follows one saved draft on this device. Change it here, save it, and the app will always reopen on that draft.</div>'''
new = '''    <label>Sleeper Draft URL or Draft ID
      <input id="draftInput" autocomplete="off">
    </label>
    <label>Admin GitHub token (this browser only)
      <input id="adminTokenInput" type="password" autocomplete="off" placeholder="Fine-grained token for wlatic/draft-center">
    </label>
    <div class="people-help">Draft, names, absent/auto flags and roast level are shared through config.json. Viewing devices read that file once when DraftCenter loads — refresh the TV whenever you want it to pick up a change. The GitHub token is stored only on this admin browser and is never written to the repo.</div>
    <div class="people-help" id="sharedSaveState"></div>'''
assert old in s, "draft settings block not found"
s = s.replace(old, new, 1)
s = s.replace('<button class="tool" id="applyDraft" type="button">Save & load draft</button>', '<button class="tool" id="applyDraft" type="button">Save shared draft</button>', 1)
s = s.replace('<button class="tool" id="savePeople" type="button">Save people</button>', '<button class="tool" id="savePeople" type="button">Save shared people</button>', 1)

old = '''  function storedDraftId(){
    try{
      const raw=localStorage.getItem("draftcenterLeagueSettings");
      const settings=raw?JSON.parse(raw):{};
      return String(settings?.draftId||DEFAULT_DRAFT_ID).replace(/\\D/g,"") || DEFAULT_DRAFT_ID;
    }catch(_){
      return DEFAULT_DRAFT_ID;
    }
  }

  let draftId = storedDraftId();'''
new = '''  const SHARED_CONFIG_URL = "https://raw.githubusercontent.com/wlatic/draft-center/main/config.json";
  const GITHUB_CONFIG_API = "https://api.github.com/repos/wlatic/draft-center/contents/config.json";

  let draftId = DEFAULT_DRAFT_ID;'''
assert old in s, "storedDraftId block not found"
s = s.replace(old, new, 1)

old = '''  function loadDraft(v){
    const m=String(v||"").match(/(\\d{10,})/);
    if(!m){
      $("status").textContent="Enter a valid Sleeper draft URL or draft ID.";
      $("status").classList.add("bad");
      return;
    }
    draftId=m[1];
    saveLeagueSettings();
    location.reload();
  }
'''
new = '''  async function loadDraft(v){
    const m=String(v||"").match(/(\\d{10,})/);
    if(!m){
      $("status").textContent="Enter a valid Sleeper draft URL or draft ID.";
      $("status").classList.add("bad");
      return;
    }
    draftId=m[1];
    roastLevel=$("roastLevel").value;
    await saveSharedSettings({reload:true});
  }
'''
assert old in s, "loadDraft block not found"
s = s.replace(old, new, 1)

old = '''  function loadLeagueSettings(){
    try{
      const raw=localStorage.getItem("draftcenterLeagueSettings");
      if(!raw)return;
      const s=JSON.parse(raw);
      absentUsernames=new Set((Array.isArray(s.absent)?s.absent:[]).map(x=>String(x).trim().toLowerCase()).filter(Boolean));
      autodraftUsernames=new Set((Array.isArray(s.autodraft)?s.autodraft:[]).map(x=>String(x).trim().toLowerCase()).filter(Boolean));
      broadcastNames=(s.broadcastNames&&typeof s.broadcastNames==="object")?s.broadcastNames:{};
      roastLevel=["off","light","spicy"].includes(s.roastLevel)?s.roastLevel:"spicy";
      if(s.draftId)draftId=String(s.draftId).replace(/\\D/g,"")||draftId;
    }catch(_){}
  }

  function saveLeagueSettings(){
    const data={
      draftId,
      absent:[...absentUsernames],
      autodraft:[...autodraftUsernames],
      broadcastNames,
      roastLevel
    };
    try{localStorage.setItem("draftcenterLeagueSettings",JSON.stringify(data));}catch(_){}
  }'''
new = '''  function applySharedSettings(cfg){
    if(!cfg||typeof cfg!=="object")return;
    const id=String(cfg.draftId||"").replace(/\\D/g,"");
    if(id)draftId=id;
    absentUsernames=new Set((Array.isArray(cfg.absent)?cfg.absent:[]).map(x=>String(x).trim().toLowerCase()).filter(Boolean));
    autodraftUsernames=new Set((Array.isArray(cfg.autodraft)?cfg.autodraft:[]).map(x=>String(x).trim().toLowerCase()).filter(Boolean));
    broadcastNames=(cfg.broadcastNames&&typeof cfg.broadcastNames==="object")?cfg.broadcastNames:{};
    roastLevel=["off","light","spicy"].includes(cfg.roastLevel)?cfg.roastLevel:"spicy";
  }

  function adminToken(){
    try{return localStorage.getItem("draftcenterAdminToken")||""}catch(_){return ""}
  }

  function rememberAdminToken(token){
    try{
      if(token)localStorage.setItem("draftcenterAdminToken",token);
      else localStorage.removeItem("draftcenterAdminToken");
    }catch(_){}
  }

  function sharedPayload(){
    return {
      draftId,
      roastLevel,
      broadcastNames,
      absent:[...absentUsernames],
      autodraft:[...autodraftUsernames]
    };
  }

  function utf8Base64(text){
    return btoa(unescape(encodeURIComponent(text)));
  }

  async function loadSharedSettings(){
    try{
      const r=await fetch(`${SHARED_CONFIG_URL}?v=${Date.now()}`,{cache:"no-store"});
      if(!r.ok)throw new Error(`config ${r.status}`);
      applySharedSettings(await r.json());
    }catch(e){
      console.warn("Shared DraftCenter config unavailable; using defaults",e);
    }
  }

  async function saveSharedSettings({reload=false}={}){
    const token=String($("adminTokenInput")?.value||adminToken()).trim();
    const state=$("sharedSaveState");
    if(!token){
      if(state)state.textContent="Admin token required to save shared settings.";
      return false;
    }
    rememberAdminToken(token);
    if(state)state.textContent="Saving shared settings…";

    try{
      const headers={
        "Accept":"application/vnd.github+json",
        "Authorization":`Bearer ${token}`,
        "X-GitHub-Api-Version":"2022-11-28"
      };
      const meta=await fetch(`${GITHUB_CONFIG_API}?ref=main&v=${Date.now()}`,{headers,cache:"no-store"});
      if(!meta.ok)throw new Error(`GitHub config read failed (${meta.status})`);
      const current=await meta.json();
      const body={
        message:"Update DraftCenter shared settings",
        content:utf8Base64(JSON.stringify(sharedPayload(),null,2)+"\\n"),
        sha:current.sha,
        branch:"main"
      };
      const put=await fetch(GITHUB_CONFIG_API,{
        method:"PUT",
        headers:{...headers,"Content-Type":"application/json"},
        body:JSON.stringify(body)
      });
      if(!put.ok){
        let detail="";
        try{detail=(await put.json())?.message||""}catch(_){}
        throw new Error(`GitHub save failed (${put.status})${detail?`: ${detail}`:""}`);
      }
      if(state)state.textContent="Shared settings saved. Refresh another device to load them.";
      if(reload)setTimeout(()=>location.reload(),900);
      return true;
    }catch(e){
      if(state)state.textContent=e.message;
      $("status").textContent=e.message;
      $("status").classList.add("bad");
      return false;
    }
  }'''
assert old in s, "league settings block not found"
s = s.replace(old, new, 1)

old = '''  function savePeopleSettings(){'''
new = '''  async function savePeopleSettings(){'''
assert old in s, "savePeopleSettings signature not found"
s = s.replace(old, new, 1)

old = '''    roastLevel=$("roastLevel").value;
    saveLeagueSettings();
    renderDash();
    $("settings").classList.remove("open");
  }'''
new = '''    roastLevel=$("roastLevel").value;
    const saved=await saveSharedSettings();
    renderDash();
    if(saved)$("settings").classList.remove("open");
  }'''
assert old in s, "savePeopleSettings body not found"
s = s.replace(old, new, 1)

old = '''  function populateLeagueSettings(){
    $("draftInput").value=`https://sleeper.com/draft/nfl/${draftId}`;
    $("roastLevel").value=roastLevel;
    $("volumeInput").value=Math.round(masterVolume*100);
    updateAudioState();
    renderPeopleSettings();
  }

  loadLeagueSettings();'''
new = '''  function populateLeagueSettings(){
    $("draftInput").value=`https://sleeper.com/draft/nfl/${draftId}`;
    $("adminTokenInput").value=adminToken();
    $("roastLevel").value=roastLevel;
    $("volumeInput").value=Math.round(masterVolume*100);
    updateAudioState();
    renderPeopleSettings();
  }'''
assert old in s, "populate/load settings block not found"
s = s.replace(old, new, 1)

old = '''  $("roastLevel").addEventListener("change",()=>{
    roastLevel=$("roastLevel").value;
    saveLeagueSettings();
  });'''
new = '''  $("roastLevel").addEventListener("change",()=>{
    roastLevel=$("roastLevel").value;
  });'''
assert old in s, "roast listener not found"
s = s.replace(old, new, 1)

old = '''  $("draftInput").value=`https://sleeper.com/draft/nfl/${draftId}`;
  pollDraft();pollPicks();
  // ADP load is started after the first draft object arrives so we can choose
  // the correct scoring format. pollDraft() will trigger it once below.
  setInterval(pollDraft,DRAFT_MS);
  setInterval(pollPicks,PICKS_MS);
  setInterval(renderClock,100);
  setInterval(eventTick,100);
  setInterval(rotateInsight,10000);'''
new = '''  async function boot(){
    // Shared league settings are loaded once per page load. There is deliberately
    // no config polling: refresh another device when you want it to pick up changes.
    await loadSharedSettings();
    $("draftInput").value=`https://sleeper.com/draft/nfl/${draftId}`;
    pollDraft();pollPicks();
    // ADP load is started after the first draft object arrives so we can choose
    // the correct scoring format. pollDraft() will trigger it once below.
    setInterval(pollDraft,DRAFT_MS);
    setInterval(pollPicks,PICKS_MS);
    setInterval(renderClock,100);
    setInterval(eventTick,100);
    setInterval(rotateInsight,10000);
  }
  boot();'''
assert old in s, "startup block not found"
s = s.replace(old, new, 1)

path.write_text(s, encoding="utf-8")
