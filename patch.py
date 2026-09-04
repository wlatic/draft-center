from pathlib import Path

p=Path('index.html')
s=p.read_text(encoding='utf-8')

s=s.replace('''  let zeroReactionPlayed = false;\n  let lastZeroPollAt = 0;''','''  let zeroReactionPlayed = false;\n  let lastZeroPollAt = 0;\n  let warningCrowdStarted = false;''')

s=s.replace('''  function playPickStinger(){\n    if(!soundEnabled)return;\n    fadeOutAudioGroup("pick",240);\n    if(Math.random()<.56)setTimeout(()=>playTags(["crowd","pick"],.38,1,"pick"),90);\n  }''','''  function playPickStinger(){\n    if(!soundEnabled)return;\n\n    // Very fast picks are intentionally silent. If this turn already reached\n    // the warning-crowd phase, the crowd reaction itself is enough and we do\n    // not add a separate pick sound on top.\n    const elapsed=(Date.now()-turnStartedAt)/1000;\n    if(elapsed<=8 || warningCrowdStarted)return;\n\n    // Keep ordinary pick audio rare and avoid the repetitive hand-clap sample.\n    fadeOutAudioGroup("pick",240);\n    if(Math.random()<.15)setTimeout(()=>playTags(["crowd","arena"],.28,1,"pick"),90);\n  }''')

s=s.replace('''    const secs=rem/1000;\n    renderPressure(secs);''','''    const secs=rem/1000;\n\n    // At 20 seconds the room starts getting restless. This is one crowd cue\n    // per turn, not a repeated sound on every render tick.\n    if(draft.status==="drafting" && secs<=20 && secs>0 && soundEnabled && !warningCrowdStarted){\n      warningCrowdStarted=true;\n      fadeOutAudioGroup("warning",220);\n      playTags(["crowd","boo"],.32,1,"warning");\n    }\n\n    renderPressure(secs);''')

s=s.replace('''        hidePressure();\n        playPickStinger();\n        activeEvent=null;''','''        hidePressure();\n        playPickStinger();\n        fadeOutAudioGroup("warning",420);\n        warningCrowdStarted=false;\n        activeEvent=null;''')

p.write_text(s,encoding='utf-8')
