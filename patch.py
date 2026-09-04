from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')


def rep(old, new, label):
    global s
    if old not in s:
        raise SystemExit(f'{label}: target not found')
    s = s.replace(old, new, 1)


# -----------------------------------------------------------------------------
# A new draft is a new room. Do not carry manager-specific aliases/flags from
# the previous draft into it.
# -----------------------------------------------------------------------------
rep(
'''    draftId=m[1];
    roastLevel=$("roastLevel").value;
    await saveSharedSettings({reload:true});''',
'''    const nextDraftId=m[1];
    const draftChanged=nextDraftId!==draftId;
    draftId=nextDraftId;

    if(draftChanged){
      broadcastNames={};
      absentUsernames=new Set();
      autodraftUsernames=new Set();
      roastDecks.clear();
      debugLog("CONFIG",`new draft ${draftId}: cleared broadcast names, absent flags and auto-draft flags`);
    }

    roastLevel=$("roastLevel").value;
    await saveSharedSettings({reload:true});''',
'draft-specific people reset'
)


# -----------------------------------------------------------------------------
# Expand the warning-boo pool. All additions below are backed by repository
# credits that identify the original Freesound files as CC0.
# -----------------------------------------------------------------------------
rep(
'''    // Both boo recordings are CC0 at their original Freesound sources. These
    // GitHub mirrors let a static DraftCenter page stream them without auth.
    {id:"boo_small_cc0",tags:["crowd","boo","warning"],url:"https://raw.githubusercontent.com/NEW-CYLANDIA/little-warioware/main/microgames/press_key/353925__dr_skitz__boo.wav"},
    {id:"boo_group_cc0",tags:["crowd","boo","warning"],url:"https://raw.githubusercontent.com/de-teiu/booing/master/js/sound/81191__payattention__booooooo.mp3"},''',
'''    // Warning-boo pool. Use a shuffle bag so every clip is heard before one
    // repeats; these mirrors are backed by CC0 source credits in their repos.
    {id:"boo_small_cc0",tags:["crowd","boo","warning"],url:"https://raw.githubusercontent.com/NEW-CYLANDIA/little-warioware/main/microgames/press_key/353925__dr_skitz__boo.wav"},
    {id:"boo_group_cc0",tags:["crowd","boo","warning"],url:"https://raw.githubusercontent.com/de-teiu/booing/master/js/sound/81191__payattention__booooooo.mp3"},
    {id:"boo_bardcraft_1_cc0",tags:["crowd","boo","warning"],url:"https://raw.githubusercontent.com/raltsmc/Bardcraft/main/sound/Bardcraft/crowd/boo1.wav"},
    {id:"boo_bardcraft_2_cc0",tags:["crowd","boo","warning"],url:"https://raw.githubusercontent.com/raltsmc/Bardcraft/main/sound/Bardcraft/crowd/boo2.wav"},
    {id:"boo_bardcraft_3_cc0",tags:["crowd","boo","warning"],url:"https://raw.githubusercontent.com/raltsmc/Bardcraft/main/sound/Bardcraft/crowd/boo3.wav"},
    {id:"boo_simonsays_cc0",tags:["crowd","boo","warning"],url:"https://raw.githubusercontent.com/juan-rey/simonsays-web/main/simonsays-board-editor/assets/sounds/boo.mp3"},''',
'expanded CC0 boo pool'
)


# -----------------------------------------------------------------------------
# Audio spacing. Event sounds should not pile on top of each other. The clock
# tick is allowed to repeat once per second, but event cues have a 2.5s floor.
# -----------------------------------------------------------------------------
rep(
'''  let lastSoundEventAt = 0;
  let insightIndex = 0;''',
'''  const NON_CLOCK_SOUND_GAP_MS = 2500;
  let lastSoundEventAt = 0;
  let insightIndex = 0;''',
'audio gap state'
)

rep(
'''    let deck=soundDecks.get(key)||[];
    deck=deck.filter(id=>matches.some(s=>s.id===id));
    if(!deck.length)deck=shuffledSounds(matches).map(s=>s.id);
    const id=deck.shift();''',
'''    let deck=soundDecks.get(key)||[];
    deck=deck.filter(id=>matches.some(s=>s.id===id));
    if(!deck.length){
      deck=shuffledSounds(matches).map(s=>s.id);
      const previous=soundRecentIds[soundRecentIds.length-1];
      if(deck.length>1 && deck[0]===previous){
        [deck[0],deck[1]]=[deck[1],deck[0]];
      }
    }
    const id=deck.shift();''',
'avoid immediate sound repeat across shuffle cycles'
)

rep(
'''  async function playTags(tags,volume=1,rate=1,group="general",deckKey=null,maxMs=0){
    if(!soundEnabled)return null;
    cleanupFinishedClips();
    const chosen=chooseSound(tags,deckKey);
    if(!chosen)return null;
    const a=makeRepoAudio(chosen,volume,rate,group);
    activeClipAudios.push(a);
    debugLog("AUDIO",`${chosen.id} · ${group} · ${Array.isArray(tags)?tags.join("+"):tags}`);
    try{await a.play()}catch(e){debugLog("AUDIO!",`${chosen.id} failed: ${e?.message||e}`)}
    if(maxMs>0)setTimeout(()=>fadeOutAudio(a,500),maxMs);
    return a;
  }''',
'''  async function playTags(tags,volume=1,rate=1,group="general",deckKey=null,maxMs=0){
    if(!soundEnabled)return null;

    const tagList=Array.isArray(tags)?tags:[tags];
    const isClock=group==="clock" || tagList.includes("tick") || tagList.includes("clock");
    const now=Date.now();

    // Keep non-clock cues separated so the room never becomes a pile of
    // whistles, boos and reactions. Clock ticks are the deliberate exception.
    if(!isClock && now-lastSoundEventAt<NON_CLOCK_SOUND_GAP_MS){
      debugLog("AUDIO-SKIP",`${group} suppressed · ${NON_CLOCK_SOUND_GAP_MS-(now-lastSoundEventAt)}ms spacing remaining`);
      return null;
    }

    cleanupFinishedClips();
    const chosen=chooseSound(tags,deckKey);
    if(!chosen)return null;

    if(!isClock)lastSoundEventAt=now;
    soundRecentIds.push(chosen.id);
    while(soundRecentIds.length>12)soundRecentIds.shift();

    const a=makeRepoAudio(chosen,volume,rate,group);
    activeClipAudios.push(a);
    debugLog("AUDIO",`${chosen.id} · ${group} · ${tagList.join("+")}`);
    try{await a.play()}catch(e){debugLog("AUDIO!",`${chosen.id} failed: ${e?.message||e}`)}
    if(maxMs>0)setTimeout(()=>fadeOutAudio(a,500),maxMs);
    return a;
  }''',
'global non-clock audio spacing'
)

rep(
'''    setTimeout(()=>playTags(["reaction","timeout"],.62,1,"test","test-reaction",2200),1200);''',
'''    setTimeout(()=>playTags(["reaction","timeout"],.62,1,"test","test-reaction",2200),3000);''',
'audio test spacing'
)

# At 10s and 5s an event cue is more useful than playing the clock click at the
# exact same instant. Skip that one tick rather than layer two sounds.
rep(
'''      if(whole>=1 && whole<=10 && whole!==lastPressureSecond){
        lastPressureSecond=whole;
        playClockTick(whole);
      }

      if(seconds<=10 && seconds>5 && pressureSoundStage<1){
        pressureSoundStage=1;
        playPressureCue(1);
      }else if(seconds<=5 && seconds>0 && pressureSoundStage<2){
        pressureSoundStage=2;
        playPressureCue(2);
      }else if(seconds<=0){
        playTimeoutReaction();
      }''',
'''      let cueFired=false;
      if(seconds<=10 && seconds>5 && pressureSoundStage<1){
        pressureSoundStage=1;
        playPressureCue(1);
        cueFired=true;
      }else if(seconds<=5 && seconds>0 && pressureSoundStage<2){
        pressureSoundStage=2;
        playPressureCue(2);
        cueFired=true;
      }else if(seconds<=0){
        playTimeoutReaction();
        cueFired=true;
      }

      if(!cueFired && whole>=1 && whole<=10 && whole!==lastPressureSecond){
        lastPressureSecond=whole;
        playClockTick(whole);
      }else if(cueFired && whole>=1 && whole<=10){
        // Mark the second consumed so it cannot tick on the next 100ms render.
        lastPressureSecond=whole;
      }''',
'prevent cue and tick collision'
)

p.write_text(s, encoding='utf-8')
print('patched draft reset, expanded boo pool, and audio spacing')
