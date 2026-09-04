from pathlib import Path

path = Path("index.html")
s = path.read_text(encoding="utf-8")


def once(old, new, label):
    global s
    if old not in s:
        raise SystemExit(f"Patch target not found: {label}")
    s = s.replace(old, new, 1)


# --- One saved draft setting; no draft query-string state ---
once(
'''    <label>Draft URL or Draft ID
      <input id="draftInput" autocomplete="off">
    </label>''',
'''    <label>Sleeper Draft URL or Draft ID
      <input id="draftInput" autocomplete="off">
    </label>
    <div class="people-help">DraftCenter follows one saved draft on this device. Change it here, save it, and the app will always reopen on that draft.</div>''',
"draft settings label",
)

once(
'''      <button class="tool" id="applyDraft" type="button">Load draft</button>''',
'''      <button class="tool" id="applyDraft" type="button">Save & load draft</button>''',
"draft button",
)

once(
'''  const DEFAULT_DRAFT_ID = "1401712491624411136";
  const API = "https://api.sleeper.app/v1";
  const PICKS_MS = 300;
  const DRAFT_MS = 1200;
  const params = new URLSearchParams(location.search);

  let draftId = (params.get("draft") || DEFAULT_DRAFT_ID).replace(/\\D/g,"") || DEFAULT_DRAFT_ID;''',
'''  const DEFAULT_DRAFT_ID = "1401712491624411136";
  const API = "https://api.sleeper.app/v1";
  const PICKS_MS = 300;
  const DRAFT_MS = 1200;

  function storedDraftId(){
    try{
      const raw=localStorage.getItem("draftcenterLeagueSettings");
      const settings=raw?JSON.parse(raw):{};
      return String(settings?.draftId||DEFAULT_DRAFT_ID).replace(/\\D/g,"") || DEFAULT_DRAFT_ID;
    }catch(_){
      return DEFAULT_DRAFT_ID;
    }
  }

  let draftId = storedDraftId();''',
"draft initialization",
)

once(
'''  function loadDraft(v){
    const m=String(v||"").match(/(\\d{10,})/);if(!m)return;
    const u=new URL(location.href);u.searchParams.set("draft",m[1]);location.href=u.toString();
  }''',
'''  function loadDraft(v){
    const m=String(v||"").match(/(\\d{10,})/);
    if(!m){
      $("status").textContent="Enter a valid Sleeper draft URL or draft ID.";
      $("status").classList.add("bad");
      return;
    }
    draftId=m[1];
    saveLeagueSettings();
    location.reload();
  }''',
"loadDraft",
)

once(
'''      broadcastNames=(s.broadcastNames&&typeof s.broadcastNames==="object")?s.broadcastNames:{};
      roastLevel=["off","light","spicy"].includes(s.roastLevel)?s.roastLevel:"spicy";''',
'''      broadcastNames=(s.broadcastNames&&typeof s.broadcastNames==="object")?s.broadcastNames:{};
      roastLevel=["off","light","spicy"].includes(s.roastLevel)?s.roastLevel:"spicy";
      if(s.draftId)draftId=String(s.draftId).replace(/\\D/g,"")||draftId;''',
"load saved draft",
)

once(
'''    const data={
      absent:[...absentUsernames],''',
'''    const data={
      draftId,
      absent:[...absentUsernames],''',
"save draft id",
)

once(
'''  function populateLeagueSettings(){
    $("roastLevel").value=roastLevel;''',
'''  function populateLeagueSettings(){
    $("draftInput").value=`https://sleeper.com/draft/nfl/${draftId}`;
    $("roastLevel").value=roastLevel;''',
"populate draft setting",
)

# --- Smooth audio cutoffs / fades ---
once(
'''  // Original procedural sports-broadcast sound engine.
  // No ESPN audio or third-party sound samples are used.''',
'''  // Real CC0 crowd/whistle/click recordings streamed from the sound bank.
  // Active clips are grouped so interruptions can fade instead of hard-cutting.''',
"audio comment",
)

once(
'''  function makeRepoAudio(sound,volume=1,rate=1){
    if(!sound)return null;
    const a=new Audio(sound.url);
    a.preload="auto";
    a.volume=Math.max(0,Math.min(1,volume*masterVolume));
    a.playbackRate=Math.max(.85,Math.min(1.2,rate));
    return a;
  }

  function cleanupFinishedClips(){
    activeClipAudios=activeClipAudios.filter(a=>!a.ended&&!a.paused);
  }

  async function playTags(tags,volume=1,rate=1){
    if(!soundEnabled)return null;
    cleanupFinishedClips();
    const chosen=chooseSound(tags);
    if(!chosen)return null;
    const a=makeRepoAudio(chosen,volume,rate);
    activeClipAudios.push(a);
    try{await a.play()}catch(_){}
    return a;
  }''',
'''  function makeRepoAudio(sound,volume=1,rate=1,group="general"){
    if(!sound)return null;
    const a=new Audio(sound.url);
    a.preload="auto";
    a.volume=Math.max(0,Math.min(1,volume*masterVolume));
    a.playbackRate=Math.max(.85,Math.min(1.2,rate));
    a._dcGroup=group;
    a._dcFading=false;
    return a;
  }

  function cleanupFinishedClips(){
    activeClipAudios=activeClipAudios.filter(a=>!a.ended&&!a.paused);
  }

  function fadeOutAudio(a,duration=350){
    if(!a||a.paused||a.ended||a._dcFading)return;
    a._dcFading=true;
    const startVolume=Math.max(0,a.volume);
    const started=performance.now();
    const step=now=>{
      if(a.paused||a.ended)return;
      const p=Math.min(1,(now-started)/Math.max(80,duration));
      a.volume=startVolume*(1-p);
      if(p>=1){
        try{a.pause();a.currentTime=0}catch(_){}
        a._dcFading=false;
        cleanupFinishedClips();
      }else requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }

  function fadeOutAudioGroup(group,duration=350){
    cleanupFinishedClips();
    activeClipAudios.filter(a=>a._dcGroup===group).forEach(a=>fadeOutAudio(a,duration));
  }

  function fadeOutAllAudio(duration=350){
    cleanupFinishedClips();
    activeClipAudios.forEach(a=>fadeOutAudio(a,duration));
  }

  async function playTags(tags,volume=1,rate=1,group="general"){
    if(!soundEnabled)return null;
    cleanupFinishedClips();
    const chosen=chooseSound(tags);
    if(!chosen)return null;
    const a=makeRepoAudio(chosen,volume,rate,group);
    activeClipAudios.push(a);
    try{await a.play()}catch(_){}
    return a;
  }''',
"audio fade helpers",
)

once(
'''    }else{
      for(const a of activeClipAudios){try{a.pause();a.currentTime=0}catch(_){} }
      activeClipAudios=[];
    }'''.replace('} }','}}'),
'''    }else{
      fadeOutAllAudio(420);
    }''',
"sound disable fade",
)

once('''    await playTags(["whistle"],.72);''','''    await playTags(["whistle"],.72,1,"test");''',"test whistle group")
once('''    setTimeout(()=>playTags(["crowd","boo"],.70),1200);''','''    setTimeout(()=>playTags(["crowd","boo"],.70,1,"test"),1200);''',"test boo group")
once('''    setTimeout(()=>playTags(["crowd","pick"],.42),3000);''','''    setTimeout(()=>playTags(["crowd","pick"],.42,1,"test"),3000);''',"test pick group")

once(
'''  function playPickStinger(){
    if(!soundEnabled)return;
    if(Math.random()<.56)playTags(["crowd","pick"],.38);
  }''',
'''  function playPickStinger(){
    if(!soundEnabled)return;
    fadeOutAudioGroup("pick",240);
    if(Math.random()<.56)setTimeout(()=>playTags(["crowd","pick"],.38,1,"pick"),90);
  }''',
"pick stinger fade",
)

once('''    playTags(["tick","clock"],volume,rate);''','''    playTags(["tick","clock"],volume,rate,"clock");''',"clock group")

once(
'''    if(stage===1){
      playTags(["whistle","pressure"],.56);
    }else if(stage===2){
      if(Math.random()<.58)playTags(["crowd","gasp"],.56);
      else playTags(["crowd","aww"],.56);
    }''',
'''    if(stage===1){
      fadeOutAudioGroup("pressure",260);
      playTags(["whistle","pressure"],.56,1,"pressure");
    }else if(stage===2){
      fadeOutAudioGroup("pressure",260);
      if(Math.random()<.58)playTags(["crowd","gasp"],.56,1,"pressure");
      else playTags(["crowd","aww"],.56,1,"pressure");
    }''',
"pressure cue fade",
)

once(
'''    if(r<.50)playTags(["crowd","boo"],.82);
    else if(r<.80)playTags(["crowd","protest"],.72);
    else playTags(["crowd","aww"],.72);''',
'''    if(r<.50)playTags(["crowd","boo"],.82,1,"timeout");
    else if(r<.80)playTags(["crowd","protest"],.72,1,"timeout");
    else playTags(["crowd","aww"],.72,1,"timeout");''',
"timeout group",
)

once(
'''    pressureShowing=false;
    $("pressure").className="";
    resetPressureSound();''',
'''    pressureShowing=false;
    $("pressure").className="";
    fadeOutAudioGroup("pressure",360);
    fadeOutAudioGroup("timeout",420);
    resetPressureSound();''',
"pressure exit fade",
)

# Settings note text
once(
'''    Sounds use real CC0 recordings streamed from GitHub rather than generated beeps.
    The People tab controls broadcast names, Absent status and Auto-draft status per Sleeper username.
    The countdown has a non-repeating phrase bag and a physical click each second from 10 to 1.''',
'''    DraftCenter follows one saved Sleeper draft configured in the Draft tab.
    The People tab controls broadcast names, Absent status and Auto-draft status per Sleeper username.
    Sounds fade out instead of stopping abruptly when a draft moment interrupts them.''',
"settings note",
)

path.write_text(s, encoding="utf-8")
print("DraftCenter patch applied")
