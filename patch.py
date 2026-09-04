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


# -----------------------------------------------------------------------------
# Settings diagnostics
# -----------------------------------------------------------------------------
rep(
'''    <button class="settings-tab" type="button" data-pane="audioPane">Audio</button>\n  </div>''',
'''    <button class="settings-tab" type="button" data-pane="audioPane">Audio</button>\n    <button class="settings-tab" type="button" data-pane="debugPane">Debug</button>\n  </div>''',
'debug tab')

rep(
'''    <div class="people-list" id="peopleList">\n      <div class="people-help">Waiting for Sleeper users…</div>\n    </div>''',
'''    <div class="people-help" id="sharedConfigSummary">Shared config not loaded yet.</div>\n    <div class="people-list" id="peopleList">\n      <div class="people-help">Waiting for Sleeper users…</div>\n    </div>''',
'people shared summary')

rep(
'''  </section>\n\n  <div class="settings-actions">\n    <button class="tool" id="closeSettings" type="button">Close</button>\n  </div>\n</div>''',
'''  </section>\n\n  <section class="settings-pane" id="debugPane">\n    <div class="people-help">Session-only diagnostics. This logs meaningful events — config/name matching, turn changes, picks, stories and the exact audio file selected. It deliberately does not log every API poll.</div>\n    <div class="people-help" id="debugSummary">Waiting for boot…</div>\n    <textarea id="debugOutput" readonly spellcheck="false" style="width:100%;height:280px;resize:vertical;background:#07111f;color:#b9d4ef;border:1px solid rgba(97,150,214,.35);border-radius:8px;padding:10px;font:10px/1.45 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;white-space:pre;"></textarea>\n    <div class="settings-actions">\n      <button class="tool" id="copyDebug" type="button">Copy log</button>\n      <button class="tool" id="clearDebug" type="button">Clear log</button>\n    </div>\n  </section>\n\n  <div class="settings-actions">\n    <button class="tool" id="closeSettings" type="button">Close</button>\n  </div>\n</div>''',
'debug pane')

rep(
'''  const roastMemory = new Map();\n  let pressureShowing = false;''',
'''  const roastMemory = new Map();\n  const roastDecks = new Map();\n  let pressureShowing = false;''',
'roast decks state')

rep(
'''  const soundHistory = [];\n\n  // Market/value claims now use Sleeper's format-specific ADP feed.''',
'''  const soundHistory = [];\n  const debugEvents = [];\n  const debugOnce = new Set();\n  let lastLoggedTurnKey = "";\n  let lastLoggedStoryKey = "";\n\n  // Market/value claims now use Sleeper's format-specific ADP feed.''',
'debug state')

rep(
'''  const initials = s => String(s||"").trim().split(/\\s+/).filter(Boolean).map(x=>x[0]).join("").slice(0,2).toUpperCase() || "—";\n\n  const normalizeName = s => String(s||"")''',
'''  const initials = s => String(s||"").trim().split(/\\s+/).filter(Boolean).map(x=>x[0]).join("").slice(0,2).toUpperCase() || "—";\n\n  function renderDebugLog(){\n    const out=$("debugOutput");\n    if(!out)return;\n    out.value=debugEvents.join("\\n");\n    out.scrollTop=out.scrollHeight;\n  }\n\n  function updateSharedConfigSummary(){\n    const names=Object.keys(broadcastNames||{}).length;\n    const text=`Shared config · draft ${draftId} · ${names} broadcast name${names===1?"":"s"} · ${absentUsernames.size} absent · ${autodraftUsernames.size} auto`;\n    const people=$("sharedConfigSummary");\n    const debug=$("debugSummary");\n    if(people)people.textContent=text;\n    if(debug)debug.textContent=text;\n  }\n\n  function debugLog(type,message){\n    const stamp=new Date().toLocaleTimeString([], {hour12:false});\n    const line=`${stamp} [${type}] ${message}`;\n    debugEvents.push(line);\n    while(debugEvents.length>250)debugEvents.shift();\n    console.log(`[DraftCenter:${type}] ${message}`);\n    renderDebugLog();\n  }\n\n  function debugLogOnce(key,type,message){\n    if(debugOnce.has(key))return;\n    debugOnce.add(key);\n    debugLog(type,message);\n  }\n\n  function logNameResolution(source="hydrate"){\n    if(!draft)return;\n    const known=new Set();\n    for(const uid of Object.keys(draft?.draft_order||{})){\n      const slot=Number(draft.draft_order[uid]);\n      const mgr=managerForSlot(slot);\n      const username=managerUsername(mgr).toLowerCase();\n      if(!username)continue;\n      known.add(username);\n      const alias=String(broadcastNames[username]||"").trim();\n      if(alias){\n        debugLogOnce(`name:${draftId}:${username}:${alias}`,"NAME",`${username} → ${alias} matched Sleeper slot ${slot} (${source})`);\n      }\n    }\n    for(const [username,alias] of Object.entries(broadcastNames||{})){\n      const key=String(username).trim().toLowerCase();\n      if(key && !known.has(key)){\n        debugLogOnce(`name-miss:${draftId}:${key}:${alias}`,"NAME?",`${key} → ${alias} has no matching Sleeper username in this draft`);\n      }\n    }\n    updateSharedConfigSummary();\n  }\n\n  const normalizeName = s => String(s||"")''',
'debug helpers')


# -----------------------------------------------------------------------------
# Broadcast aliases: make them obvious in the studio UI, while leaving the board
# itself Sleeper-native.
# -----------------------------------------------------------------------------
rep(
'''  function broadcastName(m){\n    const username=managerUsername(m).toLowerCase();\n    const mapped=String(broadcastNames[username]||"").trim();\n    return mapped || managerTitle(m);\n  }\n\n  function isAutodraftManager(m){''',
'''  function broadcastName(m){\n    const username=managerUsername(m).toLowerCase();\n    const mapped=String(broadcastNames[username]||"").trim();\n    return mapped || managerTitle(m);\n  }\n\n  function broadcastSub(m){\n    const alias=broadcastName(m);\n    const title=managerTitle(m);\n    const sub=managerSub(m);\n    const parts=[];\n    if(alias!==title && title)parts.push(title);\n    if(sub && !parts.includes(sub))parts.push(sub);\n    return parts.join(" · ");\n  }\n\n  function isAutodraftManager(m){''',
'broadcast subline')

rep(
'''    $("nowName").textContent=managerTitle(cur);\n    $("nowOwner").innerHTML=`${esc(managerSub(cur))}${isAbsentManager(cur)?'<span class="absent-chip">ABSENT</span>':""}${isAutodraftManager(cur)?'<span class="absent-chip">AUTO-DRAFT</span>':""}`;\n    $("nowMeta").innerHTML=`Draft slot ${curInfo.slot} · Pick ${curInfo.label}${((draft?.type||"snake")==="snake"&&(curInfo.pos===1||curInfo.pos===curInfo.teams))?'<span class="turn-pill">SNAKE TURN</span>':""}`;\n    $("rosterLine").textContent=rosterLine(cur.uid);\n    setImgBox($("nowAvatar"),avatarImg(cur.avatar),initials(managerTitle(cur)));\n\n    $("nextName").textContent=managerTitle(nxt);\n    $("nextOwner").textContent=managerSub(nxt);\n    $("nextMeta").textContent=`Pick ${nextInfo.label}`;\n    setImgBox($("nextAvatar"),avatarImg(nxt.avatar),initials(managerTitle(nxt)));''',
'''    $("nowName").textContent=broadcastName(cur);\n    $("nowOwner").innerHTML=`${esc(broadcastSub(cur))}${isAbsentManager(cur)?'<span class="absent-chip">ABSENT</span>':""}${isAutodraftManager(cur)?'<span class="absent-chip">AUTO-DRAFT</span>':""}`;\n    $("nowMeta").innerHTML=`Draft slot ${curInfo.slot} · Pick ${curInfo.label}${((draft?.type||"snake")==="snake"&&(curInfo.pos===1||curInfo.pos===curInfo.teams))?'<span class="turn-pill">SNAKE TURN</span>':""}`;\n    $("rosterLine").textContent=rosterLine(cur.uid);\n    setImgBox($("nowAvatar"),avatarImg(cur.avatar),initials(broadcastName(cur)));\n\n    $("nextName").textContent=broadcastName(nxt);\n    $("nextOwner").textContent=broadcastSub(nxt);\n    $("nextMeta").textContent=`Pick ${nextInfo.label}`;\n    setImgBox($("nextAvatar"),avatarImg(nxt.avatar),initials(broadcastName(nxt)));\n\n    const turnLogKey=`${curInfo.key}:${managerUsername(cur)||broadcastName(cur)}`;\n    if(turnLogKey!==lastLoggedTurnKey){\n      lastLoggedTurnKey=turnLogKey;\n      debugLog("TURN",`${curInfo.label} · ${broadcastName(cur)}${managerUsername(cur)?` (@${managerUsername(cur)})`:""}${isAbsentManager(cur)?" · ABSENT":""}${isAutodraftManager(cur)?" · AUTO":""}`);\n    }''',
'broadcast dashboard aliases')

rep(
'''      $("lastPickMeta").textContent=`Pick ${li.label} · ${managerTitle(owner)}`;''',
'''      $("lastPickMeta").textContent=`Pick ${li.label} · ${broadcastName(owner)}`;''',
'last pick alias')


# -----------------------------------------------------------------------------
# Roast engine: large non-repeating pools, generic roasts only occasionally, and
# much sharper/contextual copy when an absent manager reaches or gets ADP value.
# -----------------------------------------------------------------------------
sub(
    r'  const LIGHT_ROASTS = \[.*?\n  function managerTitle',
'''  const LIGHT_ROASTS = [\n    n=>`${n} couldn't make it tonight, so the roster is operating without supervision.`,\n    n=>`${n} is absent. The chair is empty; the picks are still legally binding.`,\n    n=>`${n} is drafting from afar. Convenient for both travel and accountability.`,\n    n=>`${n} couldn't be here, but the waiver wire will know their name soon enough.`,\n    n=>`${n} has chosen the remote-management experience. Results may vary.`,\n    n=>`${n} is not in the room to explain the plan, which may be for the best.`,\n    n=>`${n} skipped the room but kept the consequences.`,\n    n=>`${n} is absent tonight. Their lineup decisions are already working from home.`\n  ];\n\n  const SPICY_ROASTS = [\n    n=>`${n} couldn't be bothered to attend their own draft. Commitment remains undefeated.`,\n    n=>`${n} is absent, which at least gives them a ready-made excuse for this roster.`,\n    n=>`${n}'s chair is empty and somehow still showing more draft awareness than expected.`,\n    n=>`${n} couldn't make the draft. Their strategy apparently couldn't make it either.`,\n    n=>`${n} has outsourced both attendance and accountability tonight.`,\n    n=>`${n} isn't here. Conveniently, neither is anyone who can explain the plan.`,\n    n=>`${n} skipped draft night and pre-ordered three months of waiver-wire regret.`,\n    n=>`${n} is drafting remotely because bad picks are easier to defend from a safe distance.`,\n    n=>`${n} missed draft night but will absolutely be available to complain about injuries.`,\n    n=>`${n} has gone full hands-off management before Week 1. Ambitious.`,\n    n=>`${n} is absent. Their future 'I was going to take him next' messages are already scheduled.`,\n    n=>`${n} couldn't attend, so apparently the roster is being assembled by vibes and push notifications.`,\n    n=>`${n} is not here to defend this roster. The prosecution rests.`,\n    n=>`${n} skipped the draft and somehow the accountability left with them.`,\n    n=>`${n} is running the franchise like a forgotten fantasy team from 2019.`,\n    n=>`${n} isn't here, but the eventual 2-5 start has sent a representative.`,\n    n=>`${n} has achieved the rare combo of absentee ownership and extremely visible consequences.`,\n    n=>`${n} is managing from afar. So far, mostly the 'afar' part is working.`,\n    n=>`${n} couldn't make it. Neither could the coherent roster construction.`,\n    n=>`${n} skipped draft night to preserve plausible deniability.`,\n    n=>`${n} is absent and already building a strong case for 'the projections lied to me.'`,\n    n=>`${n} has delegated attendance, judgment and apparently quality control.`,\n    n=>`${n} isn't here to hear the room laugh. Technology truly is amazing.`,\n    n=>`${n} has turned fantasy football into unattended baggage.`,\n    n=>`${n} skipped the one night where pretending to have a strategy was actually required.`,\n    n=>`${n} is absent. The roster is currently being raised by the internet.`,\n    n=>`${n} couldn't show up, but their future trade offers for your best player definitely will.`,\n    n=>`${n} has chosen to draft without witnesses. Sensible legal strategy.`,\n    n=>`${n} is not here, which saves everyone the trouble of hearing why this was 'their guy.'`,\n    n=>`${n} missed draft night. The consolation bracket has noted their availability.`\n  ];\n\n  const ABSENT_REACH_ROASTS = [\n    (n,c)=>`${n} isn't even in the room and still managed to reach ${c.gap} picks. Elite remote work.`,\n    (n,c)=>`${n} travelled ${c.gap} spots up the board without travelling to draft night.`,\n    (n,c)=>`ADP called. ${n} wasn't here to answer.`,\n    (n,c)=>`${n} just paid full retail for a player the market had on clearance.`,\n    (n,c)=>`Nothing says conviction like ignoring the room and the market simultaneously.`,\n    (n,c)=>`${n} reached ${c.gap} picks from a safe distance where nobody can ask follow-up questions.`,\n    (n,c)=>`${n} isn't present, but the reach absolutely is.`,\n    (n,c)=>`The laptop has apparently developed its own scouting department. It is aggressive.`,\n    (n,c)=>`${n} saw Sleeper ADP and chose violence against arithmetic.`,\n    (n,c)=>`${n} couldn't attend draft night, but did find time to move the market backwards.`,\n    (n,c)=>`${n} has drafted ${c.player} like someone else was about to steal him ${c.gap} picks early.`,\n    (n,c)=>`Remote drafting update: the Wi-Fi works. The value discipline does not.`,\n    (n,c)=>`${n} has confused 'get your guy' with 'pay absolutely any price.'`,\n    (n,c)=>`${n} is proving you do not need to be physically present to panic.`,\n    (n,c)=>`A ${c.gap}-pick reach with no one here to explain it. That's efficient embarrassment.`,\n    (n,c)=>`${n} drafted like the ADP column was decorative.`,\n    (n,c)=>`${n} isn't here, so we'll assume this was a typo until further notice.`,\n    (n,c)=>`The market said later. ${n} said 'I can't hear you from wherever I am.'`\n  ];\n\n  const ABSENT_VALUE_ROASTS = [\n    (n,c)=>`${n} gets ${c.gap} picks of value. Even unattended franchises occasionally find a coupon.`,\n    (n,c)=>`${n} skipped draft night and the room still did them a favor.`,\n    (n,c)=>`${n} wasn't here for the slide, but will absolutely claim this was the plan.`,\n    (n,c)=>`Credit where it's due: ${n} let everybody else make the mistake first.`,\n    (n,c)=>`${n} gets bailed out by ${c.player} falling ${c.gap} spots. Please prepare for the victory lap.`,\n    (n,c)=>`${n} found value remotely. The dangerous part is the confidence this will create.`,\n    (n,c)=>`The room handed ${n} a discount and somehow they'll take full credit.`,\n    (n,c)=>`${n} wasn't present for the bargain. History will shortly be rewritten.`,\n    (n,c)=>`${n} gets one right from off-site. Alert the fantasy group chat.`,\n    (n,c)=>`A real value pick for ${n}. Unfortunately this will encourage them.`,\n    (n,c)=>`${n} waited, the player fell, and now we're all going to hear about the genius of it.`,\n    (n,c)=>`${n} gets ${c.player} well past ADP. The absentee strategy accidentally produced evidence.`,\n    (n,c)=>`Somehow not showing up has yielded ${c.gap} picks of value. Do not let ${n} build a philosophy around this.`,\n    (n,c)=>`${n} just got rewarded for doing less. Fantasy football remains deeply unfair.`\n  ];\n\n  function nextRoastLine(poolKey,arr,name,context={}){\n    let deck=roastDecks.get(poolKey)||[];\n    deck=deck.filter(i=>Number.isInteger(i)&&i>=0&&i<arr.length);\n    if(!deck.length){\n      deck=arr.map((_,i)=>i);\n      for(let i=deck.length-1;i>0;i--){\n        const j=Math.floor(Math.random()*(i+1));\n        [deck[i],deck[j]]=[deck[j],deck[i]];\n      }\n    }\n    const idx=deck.shift();\n    roastDecks.set(poolKey,deck);\n    return arr[idx](name,context);\n  }\n\n  function absentRoastStory(m,pickNo){\n    if(roastLevel==="off" || !isAbsentManager(m))return null;\n\n    const uid=m.uid||managerUsername(m)||managerTitle(m);\n    const ownCount=livePicksOnly().filter(p=>String(p.picked_by||"")===String(m.uid||"")).length;\n\n    // Generic absence jokes are seasoning, not a notification on every selection.\n    // Contextual ADP reaches/value are handled by marketStory and can break through.\n    if(ownCount<2 || ownCount%3!==0)return null;\n    const memoryKey=`absent-generic:${uid}:${ownCount}`;\n    if(storyMemory.has(memoryKey))return null;\n    storyMemory.set(memoryKey,pickNo);\n\n    const arr=roastLevel==="light"?LIGHT_ROASTS:SPICY_ROASTS;\n    const copy=nextRoastLine(`generic:${uid}:${roastLevel}`,arr,roastName(m));\n\n    return {\n      kicker:"ABSENT OWNER DESK",\n      title:String(roastName(m)).toUpperCase(),\n      sub:copy,\n      tone:"gold",\n      duration:3900,\n      priority:50,\n      storyKey:memoryKey\n    };\n  }\n\n  function managerTitle''',
    'replace roast engine')

sub(
    r'  function marketStory\(p\)\{.*?\n  \}\n\n  function detectStory',
'''  function marketStory(p){\n    const mv=marketValue(p);\n    if(!mv)return null;\n\n    const cell=cellForPick(p);\n    const pickNo=Number(cell?.ordinal || p?.pick_no || 0);\n    const delta=pickNo-mv.rank;\n    const abs=Math.abs(delta);\n    if(abs<12)return null;\n\n    const owner=ownerForPick(p);\n    const absent=isAbsentManager(owner);\n    const uid=owner.uid||managerUsername(owner)||managerTitle(owner);\n\n    // Ordinary market notes get a global cooldown. Absent-owner ADP weirdness gets\n    // its own manager/category cooldown so a truly wild reach is not suppressed by\n    // somebody else's value alert.\n    if(abs<25){\n      const key=absent\n        ? `market:absent:${uid}:${delta>0?"value":"reach"}`\n        : (delta>0?"market:value":"market:early");\n      if(!storyAllowed(key,pickNo,absent?8:4))return null;\n    }\n\n    if(absent && roastLevel!=="off"){\n      const name=roastName(owner);\n      const gap=Math.abs(Math.round(delta));\n      const context={gap,player:pickName(p),pickNo,adp:mv.rank};\n\n      if(delta<=-12){\n        const line=roastLevel==="light"\n          ? `${name} is not here to explain why this went ${gap} picks ahead of Sleeper ADP.`\n          : nextRoastLine(`reach:${uid}`,ABSENT_REACH_ROASTS,name,context);\n        return {\n          kicker:delta<=-25?"ABSENT OWNER REACH":"ABSENT OWNER GAMBLE",\n          title:`${String(name).toUpperCase()} · ${gap} AHEAD OF ADP`,\n          sub:`${pickName(p)} selected ${pickNo} · Sleeper ADP ${mv.rank.toFixed(1)}. ${line}`,\n          tone:delta<=-25?"red":"gold",duration:4200,priority:94,\n          stats:[["Selected",pickNo],["Sleeper ADP",mv.rank.toFixed(1)],["Reach",gap+" picks"]]\n        };\n      }\n\n      if(delta>=12){\n        const line=roastLevel==="light"\n          ? `${name} gets a useful discount despite not being in the room.`\n          : nextRoastLine(`value:${uid}`,ABSENT_VALUE_ROASTS,name,context);\n        return {\n          kicker:"ABSENT OWNER VALUE",\n          title:`${String(name).toUpperCase()} · ${gap} PAST ADP`,\n          sub:`${pickName(p)} selected ${pickNo} · Sleeper ADP ${mv.rank.toFixed(1)}. ${line}`,\n          tone:"green",duration:4200,priority:92,\n          stats:[["Selected",pickNo],["Sleeper ADP",mv.rank.toFixed(1)],["Value","+ "+gap+" picks"]]\n        };\n      }\n    }\n\n    if(delta>=25){\n      return {kicker:"DRAFTCENTER VALUE",title:`${pickName(p)} FALLS ${Math.round(delta)} PICKS`,sub:`Selected ${pickNo} · Sleeper ADP ${mv.rank.toFixed(1)} · ${mv.source}`,tone:"green",duration:3900,\n        stats:[["Selected",pickNo],["Sleeper ADP",mv.rank.toFixed(1)],["Value","+ "+Math.round(delta)+" picks"]]};\n    }\n    if(delta>=12){\n      return {kicker:"VALUE ALERT",title:`${Math.round(delta)} PICKS PAST ADP`,sub:`${pickName(p)} stayed on the board longer than Sleeper's market expected.`,tone:"green",duration:3500,\n        stats:[["Selected",pickNo],["Sleeper ADP",mv.rank.toFixed(1)]]};\n    }\n    if(delta<=-25){\n      return {kicker:"AGGRESSIVE PICK",title:`${Math.abs(Math.round(delta))} PICKS AHEAD OF ADP`,sub:`${pickName(p)} goes well ahead of the Sleeper market.`,tone:"red",duration:3900,\n        stats:[["Selected",pickNo],["Sleeper ADP",mv.rank.toFixed(1)]]};\n    }\n    if(delta<=-12){\n      return {kicker:"EARLY CALL",title:`${pickName(p)} GOES EARLY`,sub:`Selected ${pickNo} · Sleeper ADP ${mv.rank.toFixed(1)}.`,tone:"gold",duration:3500,\n        stats:[["Selected",pickNo],["Sleeper ADP",mv.rank.toFixed(1)],["Difference",Math.abs(Math.round(delta))+" early"]]};\n    }\n    return null;\n  }\n\n  function detectStory''',
    'contextual market roasts')

rep(
'''    if(currentRound>=5 && c.WR>=4 && c.RB<=1 && storyOnce(`identity:zeroRB:${owner.uid}`)){\n      return {kicker:"ROSTER IDENTITY",title:"ZERO-RB WATCH",sub:`${broadcastName(owner)} now has ${c.WR} WRs and ${c.RB} RB.`,tone:"cyan",duration:3300};\n    }''',
'''    if(currentRound>=5 && c.WR>=4 && c.RB===0 && storyOnce(`identity:zeroRB:${owner.uid}`)){\n      return {kicker:"ROSTER IDENTITY",title:"ZERO-RB WATCH",sub:`${broadcastName(owner)} has ${c.WR} WRs and still has not drafted an RB.`,tone:"cyan",duration:3300};\n    }\n    if(currentRound>=6 && c.WR>=4 && c.RB===1 && storyOnce(`identity:wrheavy:${owner.uid}`)){\n      return {kicker:"ROSTER IDENTITY",title:"WR-HEAVY BUILD",sub:`${broadcastName(owner)} has ${c.WR} WRs and 1 RB. That's WR-heavy — not Zero-RB.`,tone:"cyan",duration:3300};\n    }''',
'zero rb exact logic')

# Roster insight wording + broadcast aliases.
rep('''      if(c.WR>=4) facts.push({score:c.WR,title:`${managerTitle(mgr)}: ${c.WR} WRs`,detail:`Roster through ${total} selections`,tone:"hot"});''',
    '''      if(c.WR>=4) facts.push({score:c.WR,title:`${broadcastName(mgr)}: ${c.WR} WRs`,detail:`Roster through ${total} selections`,tone:"hot"});''', 'roster wr alias')
rep('''      if(c.RB>=4) facts.push({score:c.RB,title:`${managerTitle(mgr)}: ${c.RB} RBs`,detail:`Roster through ${total} selections`,tone:"hot"});''',
    '''      if(c.RB>=4) facts.push({score:c.RB,title:`${broadcastName(mgr)}: ${c.RB} RBs`,detail:`Roster through ${total} selections`,tone:"hot"});''', 'roster rb alias')
rep('''      if(c.QB>=2) facts.push({score:c.QB+0.5,title:`${managerTitle(mgr)}: ${c.QB} QBs`,detail:`Quarterback-heavy build`,tone:"alert"});''',
    '''      if(c.QB>=2) facts.push({score:c.QB+0.5,title:`${broadcastName(mgr)}: ${c.QB} QBs`,detail:`Quarterback-heavy build`,tone:"alert"});''', 'roster qb alias')
rep('''      if(c.TE>=2) facts.push({score:c.TE+0.25,title:`${managerTitle(mgr)}: ${c.TE} TEs`,detail:`Multiple tight ends already`,tone:"alert"});''',
    '''      if(c.TE>=2) facts.push({score:c.TE+0.25,title:`${broadcastName(mgr)}: ${c.TE} TEs`,detail:`Multiple tight ends already`,tone:"alert"});''', 'roster te alias')
rep('''      if(total>=5 && c.RB<=1) facts.push({score:4.4,title:`${managerTitle(mgr)}: ${c.RB} RB`,detail:`Zero-RB / light-RB build`,tone:"good"});\n      if(total>=5 && c.WR<=1) facts.push({score:4.2,title:`${managerTitle(mgr)}: ${c.WR} WR`,detail:`Very light at wide receiver`,tone:"good"});''',
    '''      if(total>=5 && c.RB===0) facts.push({score:4.4,title:`${broadcastName(mgr)}: no RB yet`,detail:`True Zero-RB build so far`,tone:"good"});\n      else if(total>=5 && c.RB===1 && c.WR>=4) facts.push({score:4.1,title:`${broadcastName(mgr)}: 1 RB / ${c.WR} WRs`,detail:`WR-heavy build`,tone:"good"});\n      if(total>=5 && c.WR===0) facts.push({score:4.2,title:`${broadcastName(mgr)}: no WR yet`,detail:`No wide receiver selected yet`,tone:"good"});\n      else if(total>=5 && c.WR===1 && c.RB>=4) facts.push({score:4.0,title:`${broadcastName(mgr)}: 1 WR / ${c.RB} RBs`,detail:`RB-heavy build`,tone:"good"});''',
    'roster light labels')
rep('''            title:`${managerTitle(mgr)}: ${team} stack`,''', '''            title:`${broadcastName(mgr)}: ${team} stack`,''', 'stack alias')
rep('''            title:`${managerTitle(mgr)}: ${players.length} ${team} players`,''', '''            title:`${broadcastName(mgr)}: ${players.length} ${team} players`,''', 'homer alias')
rep('''        sub:`${leaderText}${valueText} Next: ${managerTitle(nextMgr)} at ${nextInfo.label}.`,''',
    '''        sub:`${leaderText}${valueText} Next: ${broadcastName(nextMgr)} at ${nextInfo.label}.`,''',
    'round recap alias')

# Preserve contextual market story priority instead of flattening it.
rep('''    if(market) candidates.push({...market,priority:90});''',
    '''    if(market) candidates.push({...market,priority:Number(market.priority||90)});''',
    'market priority')


# -----------------------------------------------------------------------------
# Audio: remove the questionable stadium/soccer-like recording entirely. Use two
# explicitly CC0 boo recordings mirrored on GitHub, rotate them without immediate
# repetition, cap the 20-second warning length, and make zero a short individual
# reaction rather than another group vocal. The clock tick remains intentionally
# repeatable.
# -----------------------------------------------------------------------------
sub(
    r'  const SOUND_CATALOG = \[.*?\];',
'''  const SOUND_CATALOG = [\n    {id:"whistle_attention",tags:["whistle","pressure"],url:"https://raw.githubusercontent.com/Wh1teDuke/WilhelmSFX/master/Samples/256552__skiggz__attention-whistle.wav"},\n    {id:"whistle_frisko",tags:["whistle","pressure"],url:"https://raw.githubusercontent.com/Wh1teDuke/WilhelmSFX/master/Samples/417392__frisko28i__whiste.wav"},\n    {id:"whistle_male",tags:["whistle","pressure"],url:"https://raw.githubusercontent.com/Wh1teDuke/WilhelmSFX/master/Samples/132294__j_bond__male-whistle.wav"},\n    {id:"whistle_pfiff",tags:["whistle","pressure"],url:"https://raw.githubusercontent.com/Wh1teDuke/WilhelmSFX/master/Samples/19825__tommorawe__pfiff_whistle.wav"},\n\n    // Both boo recordings are CC0 at their original Freesound sources. These\n    // GitHub mirrors let a static DraftCenter page stream them without auth.\n    {id:"boo_small_cc0",tags:["crowd","boo","warning"],url:"https://raw.githubusercontent.com/NEW-CYLANDIA/little-warioware/main/microgames/press_key/353925__dr_skitz__boo.wav"},\n    {id:"boo_group_cc0",tags:["crowd","boo","warning"],url:"https://raw.githubusercontent.com/de-teiu/booing/master/js/sound/81191__payattention__booooooo.mp3"},\n\n    {id:"gasp_zerocarina",tags:["reaction","pressure","timeout"],url:"https://raw.githubusercontent.com/Wh1teDuke/WilhelmSFX/master/Samples/232263__zerocarina__gasp.wav"},\n    {id:"gasp_drskitz",tags:["reaction","pressure","timeout"],url:"https://raw.githubusercontent.com/Wh1teDuke/WilhelmSFX/master/Samples/353924__dr_skitz__gasp.wav"},\n    {id:"gasp_big",tags:["reaction","timeout"],url:"https://raw.githubusercontent.com/Wh1teDuke/WilhelmSFX/master/Samples/343878__reitanna__big-gasp.wav"},\n    {id:"reaction_ooh",tags:["reaction","pressure","timeout"],url:"https://raw.githubusercontent.com/Wh1teDuke/WilhelmSFX/master/Samples/323707__reitanna__ooh.wav"},\n    {id:"reaction_disappointed",tags:["reaction","timeout"],url:"https://raw.githubusercontent.com/Wh1teDuke/WilhelmSFX/master/Samples/170765__esperar__oh-disappointed.wav"},\n    {id:"reaction_sigh",tags:["reaction","timeout"],url:"https://raw.githubusercontent.com/Wh1teDuke/WilhelmSFX/master/Samples/252224__reitanna__defeated-sigh.wav"},\n\n    {id:"clock_click",tags:["tick","clock"],url:"https://raw.githubusercontent.com/Wh1teDuke/WilhelmSFX/master/Samples/107806__j1987__metallicclick.wav"}\n  ];''',
    'replace sound catalog')

sub(
    r'  async function playTags\(tags,volume=1,rate=1,group="general",deckKey=null\)\{.*?\n  \}',
'''  async function playTags(tags,volume=1,rate=1,group="general",deckKey=null,maxMs=0){\n    if(!soundEnabled)return null;\n    cleanupFinishedClips();\n    const chosen=chooseSound(tags,deckKey);\n    if(!chosen)return null;\n    const a=makeRepoAudio(chosen,volume,rate,group);\n    activeClipAudios.push(a);\n    debugLog("AUDIO",`${chosen.id} · ${group} · ${Array.isArray(tags)?tags.join("+"):tags}`);\n    try{await a.play()}catch(e){debugLog("AUDIO!",`${chosen.id} failed: ${e?.message||e}`)}\n    if(maxMs>0)setTimeout(()=>fadeOutAudio(a,500),maxMs);\n    return a;\n  }''',
    'playTags logging and cap')

sub(
    r'  async function playAudioTest\(\)\{.*?\n  \}\n\n  function playTinyConfirm',
'''  async function playAudioTest(){\n    if(!soundEnabled)return;\n    await playTags(["whistle","pressure"],.72,1,"test","test-whistle",1800);\n    setTimeout(()=>playTags(["reaction","timeout"],.62,1,"test","test-reaction",2200),1200);\n  }\n\n  function playTinyConfirm''',
    'audio test')

sub(
    r'  function playPressureCue\(stage\)\{.*?\n  \}\n\n  function playTimeoutReaction\(\)\{.*?\n  \}',
'''  function playPressureCue(stage){\n    if(!soundEnabled)return;\n    if(stage===1){\n      fadeOutAudioGroup("pressure",260);\n      playTags(["whistle","pressure"],.56,1,"pressure","pressure-whistle",2200);\n    }else if(stage===2){\n      fadeOutAudioGroup("pressure",260);\n      playTags(["reaction","pressure"],.56,1,"pressure","pressure-reaction",2200);\n    }\n  }\n\n  function playTimeoutReaction(){\n    if(!soundEnabled||zeroReactionPlayed)return;\n    zeroReactionPlayed=true;\n    // No group chant/crowd vocal at zero. One short human reaction only.\n    playTags(["reaction","timeout"],.70,1,"timeout","timeout-reaction",2600);\n  }''',
    'pressure and timeout audio')

rep(
'''      const family=chooseReactionFamily(["boo","aww","gasp"],"warning-reaction-families");\n      const volume=(family==="boo"?.34:.28);\n      playTags(["crowd",family],volume,1,"warning",`warning-${family}`);''',
'''      // The warning is specifically booing. Rotate two verified CC0 boo clips\n      // and fade them before the final countdown takes over.\n      playTags(["crowd","boo"],.32,1,"warning","warning-boo",8500);''',
'20-second warning audio')


# -----------------------------------------------------------------------------
# Shared config/name diagnostics + event logging.
# -----------------------------------------------------------------------------
rep(
'''    broadcastNames=(cfg.broadcastNames&&typeof cfg.broadcastNames==="object")?cfg.broadcastNames:{};''',
'''    broadcastNames=Object.fromEntries(\n      Object.entries((cfg.broadcastNames&&typeof cfg.broadcastNames==="object")?cfg.broadcastNames:{})\n        .map(([k,v])=>[String(k).trim().toLowerCase(),String(v||"").trim()])\n        .filter(([k,v])=>k&&v)\n    );''',
'normalize broadcast names')

rep(
'''      applySharedSettings(await r.json());''',
'''      const cfg=await r.json();\n      applySharedSettings(cfg);\n      debugLog("CONFIG",`loaded shared config: draft ${draftId}, ${Object.keys(broadcastNames).length} names, ${absentUsernames.size} absent, ${autodraftUsernames.size} auto`);\n      updateSharedConfigSummary();''',
'config load logging')

rep(
'''      if(state)state.textContent="Shared settings saved. Refresh another device to load them.";''',
'''      if(state)state.textContent="Shared settings saved. Refresh another device to load them.";\n      debugLog("CONFIG",`saved shared config: draft ${draftId}, ${Object.keys(broadcastNames).length} names, ${absentUsernames.size} absent, ${autodraftUsernames.size} auto`);\n      updateSharedConfigSummary();''',
'config save logging')

rep(
'''    renderAll();\n    if($("settings")?.classList.contains("open"))renderPeopleSettings();\n  }\n\n  async function pollDraft(){''',
'''    renderAll();\n    logNameResolution("hydrate");\n    if($("settings")?.classList.contains("open"))renderPeopleSettings();\n  }\n\n  async function pollDraft(){''',
'hydrate name logging')

rep(
'''      draft=d;\n      const newField=adpFieldForDraft();''',
'''      draft=d;\n      if(firstDraft){\n        debugLog("DRAFT",`loaded ${draftId} · ${draft?.settings?.teams||"?"} teams · ${draft?.settings?.rounds||"?"} rounds · timer ${draft?.settings?.pick_timer||0}s · status ${draft?.status||"unknown"}`);\n      }\n      const newField=adpFieldForDraft();''',
'draft load logging')

rep(
'''            const mgr=managerTitle(ownerForPick(p));\n            observedPickTimes.push({''',
'''            const pickOwner=ownerForPick(p);\n            const mgr=broadcastName(pickOwner);\n            const mv=marketValue(p);\n            const ordinal=Number(cell?.ordinal||p.pick_no||0);\n            const delta=mv?ordinal-Number(mv.rank):null;\n            debugLog("PICK",`${cell?.label||formatCellLabel(p)} · ${pickName(p)} (${p?.metadata?.position||"—"}) · ${mgr}${managerUsername(pickOwner)?` @${managerUsername(pickOwner)}`:""}${mv?` · ADP ${mv.rank.toFixed(1)} · ${delta>=0?"+":""}${Math.round(delta)}`:""}${isAutodraftManager(pickOwner)?" · AUTO-MARKED":""}`);\n            observedPickTimes.push({''',
'pick logging')

# Log takeover/studio graphics once per activation.
rep(
'''  function renderTakeover(){\n    const t=$("takeover");\n    if(!activeEvent){t.className="";t.innerHTML="";return;}\n    t.className=`show ${activeEvent.tone||""}`;''',
'''  function renderTakeover(){\n    const t=$("takeover");\n    if(!activeEvent){t.className="";t.innerHTML="";lastLoggedStoryKey="";return;}\n    const logKey=`${activeEvent.pickNo||""}:${activeEvent.kicker||""}:${activeEvent.title||""}:${activeEvent.deferredReplay?"replay":"live"}`;\n    if(logKey!==lastLoggedStoryKey){\n      lastLoggedStoryKey=logKey;\n      debugLog("STORY",`${activeEvent.kicker||""} · ${activeEvent.title||""}${activeEvent.deferredReplay?" · REPLAY":""}`);\n    }\n    t.className=`show ${activeEvent.tone||""}`;''',
'story logging')

# Settings panel summary and debug controls.
rep(
'''    updateAudioState();\n    renderPeopleSettings();\n  }''',
'''    updateAudioState();\n    renderPeopleSettings();\n    updateSharedConfigSummary();\n    renderDebugLog();\n  }''',
'populate debug summary')

rep(
'''      if(tab.dataset.pane==="peoplePane")renderPeopleSettings();\n      if(tab.dataset.pane==="audioPane")updateAudioState();''',
'''      if(tab.dataset.pane==="peoplePane"){renderPeopleSettings();updateSharedConfigSummary();}\n      if(tab.dataset.pane==="audioPane")updateAudioState();\n      if(tab.dataset.pane==="debugPane"){updateSharedConfigSummary();renderDebugLog();}''',
'debug tab behavior')

rep(
'''  $("settingsSoundBtn").addEventListener("click",async()=>await setSoundEnabled(!soundEnabled));''',
'''  $("copyDebug").addEventListener("click",async()=>{\n    const text=debugEvents.join("\\n");\n    try{await navigator.clipboard.writeText(text);debugLog("DEBUG","log copied to clipboard")}catch(_){\n      const out=$("debugOutput");if(out){out.focus();out.select();document.execCommand("copy");}\n    }\n  });\n  $("clearDebug").addEventListener("click",()=>{debugEvents.length=0;renderDebugLog();});\n  $("settingsSoundBtn").addEventListener("click",async()=>await setSoundEnabled(!soundEnabled));''',
'debug controls')

rep(
'''    await loadSharedSettings();\n    $("draftInput").value=`https://sleeper.com/draft/nfl/${draftId}`;''',
'''    await loadSharedSettings();\n    debugLog("BOOT",`DraftCenter session started for ${draftId}`);\n    $("draftInput").value=`https://sleeper.com/draft/nfl/${draftId}`;''',
'boot logging')

p.write_text(s, encoding='utf-8')
print('DraftCenter patch applied successfully')
