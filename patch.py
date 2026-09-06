from pathlib import Path
p=Path('index.html')
s=p.read_text(encoding='utf-8')

def rep(old,new,label):
    global s
    if old not in s: raise SystemExit(f'{label}: target not found')
    s=s.replace(old,new,1)

rep(
'''  function installYahooTeams(teams){\n    const order={};''',
'''  function inferYahooDraftSlots(teams,raw){\n    // Yahoo's team collection is not guaranteed to expose draft_position. Once\n    // Round 1 begins, draft_result.pick is the authoritative slot order. Use it\n    // so the TV rows cannot silently follow team_id order instead.\n    const fromResults=new Map();\n    for(const r of raw||[]){\n      if(Number(r.round)!==1)continue;\n      const slot=Number(r.pick||0);\n      if(r.teamKey && slot>0)fromResults.set(String(r.teamKey),slot);\n    }\n    return teams.map(t=>fromResults.has(String(t.teamKey))?{...t,slot:fromResults.get(String(t.teamKey))}:t);\n  }\n\n  function installYahooTeams(teams){\n    const order={};''',
'infer yahoo slots'
)

rep(
'''    const metaDoc=yahooXml(metaText),settingsDoc=yahooXml(settingsText),teamsDoc=yahooXml(teamsText),draftDoc=yahooXml(draftText);\n    const teams=parseYahooTeams(teamsDoc);\n    if(!teams.length)throw new Error("Yahoo returned no fantasy teams for that league.");\n    const order=installYahooTeams(teams);\n    const raw=parseYahooDraftResults(draftDoc);''',
'''    const metaDoc=yahooXml(metaText),settingsDoc=yahooXml(settingsText),teamsDoc=yahooXml(teamsText),draftDoc=yahooXml(draftText);\n    const raw=parseYahooDraftResults(draftDoc);\n    let teams=parseYahooTeams(teamsDoc);\n    if(!teams.length)throw new Error("Yahoo returned no fantasy teams for that league.");\n    teams=inferYahooDraftSlots(teams,raw);\n    const order=installYahooTeams(teams);''',
'use yahoo slots'
)

p.write_text(s,encoding='utf-8')
print('Yahoo draft rows now infer authoritative slot order from Round 1 results')
