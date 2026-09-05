from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')


def rep(old, new, label):
    global s
    if old not in s:
        raise SystemExit(f'{label}: target not found')
    s = s.replace(old, new, 1)


rep(
'''  const GITHUB_CONFIG_API = "https://api.github.com/repos/wlatic/draft-center/contents/config.json";\n  const PENDING_DRAFT_SESSION_KEY = "draftcenter.pendingDraftId";''',
'''  const GITHUB_CONFIG_API = "https://api.github.com/repos/wlatic/draft-center/contents/config.json";\n  const PENDING_DRAFT_SESSION_KEY = "draftcenter.pendingDraftId";\n  // AI analysis is produced by a GitHub Actions watcher on a non-Pages branch.\n  // It is deliberately optional: if this feed is unavailable, the deterministic\n  // DraftCenter panels continue to work normally.\n  const AI_ANALYSIS_URL = "https://raw.githubusercontent.com/wlatic/draft-center/analysis/analysis.json";''',
'ai analysis URL'
)

rep(
'''  let insightIndex = 0;\n  let insightSlides = [];\n  let lastInsightBuildPickCount = -1;''',
'''  let insightIndex = 0;\n  let insightSlides = [];\n  let lastInsightBuildPickCount = -1;\n  let aiAnalysis = null;\n  let lastAiRevision = "";''',
'ai analysis state'
)

rep(
'''  function debugLogOnce(key,type,message){\n    if(debugOnce.has(key))return;\n    debugOnce.add(key);\n    debugLog(type,message);\n  }\n\n  function logNameResolution(source="hydrate"){''',
'''  function debugLogOnce(key,type,message){\n    if(debugOnce.has(key))return;\n    debugOnce.add(key);\n    debugLog(type,message);\n  }\n\n  function aiAnalysisPanel(){\n    if(!aiAnalysis || String(aiAnalysis.draftId||"")!==String(draftId))return null;\n    const items=Array.isArray(aiAnalysis.items)?aiAnalysis.items:[];\n    if(!items.length)return null;\n    const age=Date.now()-Date.parse(aiAnalysis.updatedAt||0);\n    if(Number.isFinite(age) && age>20*60*1000)return null;\n    return {\n      label:"AI Draft Desk",\n      kicker:String(aiAnalysis.headline||"LIVE ANALYSIS").slice(0,72),\n      rows:items.slice(0,4).map(x=>({\n        title:String(x?.title||""),\n        detail:String(x?.detail||""),\n        tone:String(x?.tone||"")\n      }))\n    };\n  }\n\n  async function pollAIAnalysis(){\n    try{\n      const data=await fetchJsonWithTimeout(AI_ANALYSIS_URL,3500);\n      if(!data || String(data.draftId||"")!==String(draftId))return;\n      const revision=String(data.revision||data.updatedAt||"");\n      if(revision && revision===lastAiRevision)return;\n      aiAnalysis=data;\n      lastAiRevision=revision;\n      debugLog("AI",`analysis loaded · round ${data.round||"?"} · ${Array.isArray(data.items)?data.items.length:0} facts · ${data.model||"deterministic"}`);\n      // A newly-produced studio read is worth showing promptly; after that it\n      // rejoins the normal panel rotation.\n      insightIndex=0;\n      renderInsight();\n    }catch(e){\n      debugLogOnce(`ai-feed:${draftId}`,"AI!",`analysis feed unavailable; deterministic desk remains active`);\n    }\n  }\n\n  function logNameResolution(source="hydrate"){''',
'ai polling functions'
)

rep(
'''  function buildInsightPanels(){\n    const panels=[];\n\n    const round=roundFacts();\n    if(round.length) panels.push({label:"This Round",kicker:`ROUND ${currentRoundNumber()}`,rows:round});''',
'''  function buildInsightPanels(){\n    const panels=[];\n\n    const ai=aiAnalysisPanel();\n    if(ai)panels.push(ai);\n\n    const round=roundFacts();\n    if(round.length) panels.push({label:"This Round",kicker:`ROUND ${currentRoundNumber()}`,rows:round});''',
'ai desk panel priority'
)

rep(
'''    marketReady=false;\n    adpRows=[];\n    sleeperAdpById={};\n    adpAttemptedFor="";\n    turnStartedAt=Date.now();''',
'''    marketReady=false;\n    adpRows=[];\n    sleeperAdpById={};\n    adpAttemptedFor="";\n    aiAnalysis=null;\n    lastAiRevision="";\n    turnStartedAt=Date.now();''',
'clear AI state on draft switch'
)

rep(
'''    renderAll();\n    hydrate();\n    loadSleeperADP();\n    pollPicks();\n  }''',
'''    renderAll();\n    hydrate();\n    loadSleeperADP();\n    pollPicks();\n    pollAIAnalysis();\n  }''',
'poll AI on draft switch'
)

rep(
'''    setInterval(renderClock,100);\n    setInterval(eventTick,100);\n    setInterval(rotateInsight,10000);''',
'''    setInterval(renderClock,100);\n    setInterval(eventTick,100);\n    setInterval(rotateInsight,10000);\n    // The Muse worker generally publishes within seconds of a new pick. Twelve\n    // seconds keeps the TV current without making AI a dependency of the draft.\n    pollAIAnalysis();\n    setInterval(pollAIAnalysis,12000);''',
'AI polling boot'
)

p.write_text(s, encoding='utf-8')
print('wired optional Muse AI Draft Desk feed into dashboard')
