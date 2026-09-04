from pathlib import Path

p=Path('index.html')
s=p.read_text(encoding='utf-8')

old='''  const pressurePhraseBags={};
  let pressurePhraseTurnKey="";

  function shuffledCopy(arr){
    const x=[...arr];
    for(let i=x.length-1;i>0;i--){
      const j=Math.floor(Math.random()*(i+1));
      [x[i],x[j]]=[x[j],x[i]];
    }
    return x;
  }

  function pressurePhrase(stage,turnKey){
    if(pressurePhraseTurnKey!==turnKey)pressurePhraseTurnKey=turnKey;
    if(!pressurePhraseBags[stage]||!pressurePhraseBags[stage].length){
      pressurePhraseBags[stage]=shuffledCopy(PRESSURE_PHRASES[stage]||PRESSURE_PHRASES.ten);
    }
    return pressurePhraseBags[stage].shift();
  }
'''
new='''  const pressurePhraseBags={};
  const pressurePhraseCache=new Map();
  PRESSURE_PHRASES.countdown=[...PRESSURE_PHRASES.ten,...PRESSURE_PHRASES.five,...PRESSURE_PHRASES.three];

  function shuffledCopy(arr){
    const x=[...arr];
    for(let i=x.length-1;i>0;i--){
      const j=Math.floor(Math.random()*(i+1));
      [x[i],x[j]]=[x[j],x[i]];
    }
    return x;
  }

  function pressurePhrase(stage,turnKey,pool=null){
    const cacheKey=`${turnKey}:${stage}`;
    if(pressurePhraseCache.has(cacheKey))return pressurePhraseCache.get(cacheKey);

    const source=pool||PRESSURE_PHRASES[stage]||PRESSURE_PHRASES.countdown;
    if(!pressurePhraseBags[stage]||!pressurePhraseBags[stage].length){
      pressurePhraseBags[stage]=shuffledCopy(source);
    }
    const phrase=pressurePhraseBags[stage].shift();
    pressurePhraseCache.set(cacheKey,phrase);

    // Keep the cache bounded across a long draft.
    if(pressurePhraseCache.size>80){
      const oldest=pressurePhraseCache.keys().next().value;
      pressurePhraseCache.delete(oldest);
    }
    return phrase;
  }
'''
if old not in s:
    raise SystemExit('pressure phrase helper block not found')
s=s.replace(old,new,1)

old='''      const key="auto-pressure";
      if(!pressurePhraseBags[key]||!pressurePhraseBags[key].length)pressurePhraseBags[key]=shuffledCopy(autoPool);
      $("pressureSub").textContent=pressurePhraseBags[key].shift();
'''
new='''      $("pressureSub").textContent=pressurePhrase("auto",turnKey,autoPool);
'''
if old not in s:
    raise SystemExit('auto pressure block not found')
s=s.replace(old,new,1)

old='''      const key="absent-pressure";
      if(!pressurePhraseBags[key]||!pressurePhraseBags[key].length)pressurePhraseBags[key]=shuffledCopy(absentPool);
      $("pressureSub").textContent=pressurePhraseBags[key].shift();
    }else if(seconds<=3){
      $("pressureSub").textContent=pressurePhrase("three",turnKey);
    }else if(seconds<=5){
      $("pressureSub").textContent=pressurePhrase("five",turnKey);
    }else{
      $("pressureSub").textContent=pressurePhrase("ten",turnKey);
    }
'''
new='''      $("pressureSub").textContent=pressurePhrase("absent",turnKey,absentPool);
    }else{
      // One line per turn. The countdown numbers change; the copy does not spam.
      $("pressureSub").textContent=pressurePhrase("countdown",turnKey);
    }
'''
if old not in s:
    raise SystemExit('absent/general pressure block not found')
s=s.replace(old,new,1)

p.write_text(s,encoding='utf-8')
