from pathlib import Path

p=Path('index.html')
s=p.read_text(encoding='utf-8')

# Remove the soccer goal/chant clip from the catalog entirely.
s=s.replace(',{"id":"crowd_arena","tags":["crowd","arena","pick"],"url":"https://raw.githubusercontent.com/Wh1teDuke/WilhelmSFX/master/Samples/113698__huubjeroen__goalloop.wav"}', '')

# Replace the old global recent-list chooser with shuffle bags keyed by sound role.
old='''  function chooseSound(tags){
    const matches=soundsWithTags(tags);
    if(!matches.length)return null;
    let choices=matches.filter(s=>!soundRecentIds.includes(s.id));
    if(!choices.length)choices=matches;
    const chosen=choices[Math.floor(Math.random()*choices.length)];
    soundRecentIds.push(chosen.id);
    while(soundRecentIds.length>4)soundRecentIds.shift();
    return chosen;
  }
'''
new='''  const soundDecks=new Map();
  let lastReactionFamily="";

  function shuffledSounds(items){
    const x=[...items];
    for(let i=x.length-1;i>0;i--){
      const j=Math.floor(Math.random()*(i+1));
      [x[i],x[j]]=[x[j],x[i]];
    }
    return x;
  }

  function chooseSound(tags,deckKey=null){
    const matches=soundsWithTags(tags);
    if(!matches.length)return null;
    const key=deckKey||tags.join(":");
    let deck=soundDecks.get(key)||[];
    deck=deck.filter(id=>matches.some(s=>s.id===id));
    if(!deck.length)deck=shuffledSounds(matches).map(s=>s.id);
    const id=deck.shift();
    soundDecks.set(key,deck);
    return matches.find(s=>s.id===id)||matches[0];
  }

  function chooseReactionFamily(allowed,deckKey){
    let deck=soundDecks.get(deckKey)||[];
    deck=deck.filter(x=>allowed.includes(x));
    if(!deck.length){
      deck=shuffledSounds(allowed.filter(x=>x!==lastReactionFamily));
      if(!deck.length)deck=shuffledSounds(allowed);
    }
    const family=deck.shift();
    soundDecks.set(deckKey,deck);
    lastReactionFamily=family;
    return family;
  }
'''
if old not in s: raise SystemExit('chooseSound block not found')
s=s.replace(old,new)

# Allow callers to identify a deck so each role cycles independently.
s=s.replace('''  async function playTags(tags,volume=1,rate=1,group="general"){
    if(!soundEnabled)return null;
    cleanupFinishedClips();
    const chosen=chooseSound(tags);''','''  async function playTags(tags,volume=1,rate=1,group="general",deckKey=null){
    if(!soundEnabled)return null;
    cleanupFinishedClips();
    const chosen=chooseSound(tags,deckKey);''')

# Picks are silent. Draft audio comes from clock pressure, not every selection.
old='''  function playPickStinger(){
    if(!soundEnabled)return;

    // Very fast picks are intentionally silent. If this turn already reached
    // the warning-crowd phase, the crowd reaction itself is enough and we do
    // not add a separate pick sound on top.
    const elapsed=(Date.now()-turnStartedAt)/1000;
    if(elapsed<=8 || warningCrowdStarted)return;

    // Keep ordinary pick audio rare and avoid the repetitive hand-clap sample.
    fadeOutAudioGroup("pick",240);
    if(Math.random()<.15)setTimeout(()=>playTags(["crowd","arena"],.28,1,"pick"),90);
  }
'''
new='''  function playPickStinger(){
    // Intentionally silent. Pick reveals do not need a generic audio sting.
    // If the clock created pressure, those warning sounds fade when the pick lands.
  }
'''
if old not in s: raise SystemExit('playPickStinger block not found')
s=s.replace(old,new)

# Whistles cycle through all whistle recordings before reuse.
s=s.replace('playTags(["whistle","pressure"],.56,1,"pressure");','playTags(["whistle","pressure"],.56,1,"pressure","pressure-whistle");')

# Stage-two reaction alternates families and exhausts available clips within each family.
old='''      if(Math.random()<.58)playTags(["crowd","gasp"],.56,1,"pressure");
      else playTags(["crowd","aww"],.56,1,"pressure");'''
new='''      const family=chooseReactionFamily(["gasp","aww"],"pressure-reaction-families");
      playTags(["crowd",family],.56,1,"pressure",`pressure-${family}`);'''
if old not in s: raise SystemExit('pressure reaction block not found')
s=s.replace(old,new)

# Timeout also rotates families instead of repeatedly selecting the single boo clip.
old='''    const r=Math.random();
    if(r<.50)playTags(["crowd","boo"],.82,1,"timeout");
    else if(r<.80)playTags(["crowd","protest"],.72,1,"timeout");
    else playTags(["crowd","aww"],.72,1,"timeout");'''
new='''    const family=chooseReactionFamily(["boo","protest","aww","gasp"],"timeout-reaction-families");
    const volume=(family==="boo"?.82:family==="protest"?.72:.68);
    playTags(["crowd",family],volume,1,"timeout",`timeout-${family}`);'''
if old not in s: raise SystemExit('timeout block not found')
s=s.replace(old,new)

# 20-second warning rotates through several human crowd reactions, with no same family
# until the warning family deck cycles. This replaces the one boo sound every turn.
old='''      fadeOutAudioGroup("warning",220);
      playTags(["crowd","boo"],.32,1,"warning");'''
new='''      fadeOutAudioGroup("warning",220);
      const family=chooseReactionFamily(["boo","protest","aww","gasp"],"warning-reaction-families");
      const volume=(family==="boo"?.34:family==="protest"?.30:.28);
      playTags(["crowd",family],volume,1,"warning",`warning-${family}`);'''
if old not in s: raise SystemExit('warning block not found')
s=s.replace(old,new)

# Test sound should demonstrate variety, not applause/soccer.
s=s.replace('''    await playTags(["whistle"],.72,1,"test");
    setTimeout(()=>playTags(["crowd","boo"],.70,1,"test"),1200);
    setTimeout(()=>playTags(["crowd","pick"],.42,1,"test"),3000);''','''    await playTags(["whistle","pressure"],.72,1,"test","test-whistle");
    setTimeout(()=>{
      const family=chooseReactionFamily(["boo","protest","aww","gasp"],"test-reaction-families");
      playTags(["crowd",family],.62,1,"test",`test-${family}`);
    },1200);''')

p.write_text(s,encoding='utf-8')
