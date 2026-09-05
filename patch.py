from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')


def rep(old, new, label):
    global s
    if old not in s:
        raise SystemExit(f'{label}: target not found')
    s = s.replace(old, new, 1)


# -----------------------------------------------------------------------------
# Startup/config stability
# Keep same-origin GitHub Pages config first because some TV/browser setups have
# already shown problems reaching raw.githubusercontent.com during boot.
# A one-session pending-draft override prevents a just-saved draft from reverting
# while GitHub Pages catches up to the config commit.
# -----------------------------------------------------------------------------
rep(
'''  const SHARED_CONFIG_FALLBACK_URL = "https://raw.githubusercontent.com/wlatic/draft-center/main/config.json";\n  const GITHUB_CONFIG_API = "https://api.github.com/repos/wlatic/draft-center/contents/config.json";''',
'''  const SHARED_CONFIG_FALLBACK_URL = "https://raw.githubusercontent.com/wlatic/draft-center/main/config.json";\n  const GITHUB_CONFIG_API = "https://api.github.com/repos/wlatic/draft-center/contents/config.json";\n  const PENDING_DRAFT_SESSION_KEY = "draftcenter.pendingDraftId";''',
'pending draft session key'
)

rep(
'''  async function loadSharedSettings(){\n    // Raw main is the source of truth. GitHub Pages can lag behind config.json\n    // while a Pages deployment is rebuilding, which previously made a newly\n    // saved draft appear to revert to the previous draft on reload.\n    const sources=[\n      ["GitHub raw",SHARED_CONFIG_FALLBACK_URL],\n      ["GitHub Pages fallback",SHARED_CONFIG_URL]\n    ];''',
'''  async function loadSharedSettings(){\n    // Same-origin config is the most reliable startup path, especially on TV\n    // browsers. Raw GitHub remains a bounded fallback, never a boot dependency.\n    const sources=[\n      ["GitHub Pages",SHARED_CONFIG_URL],\n      ["GitHub raw fallback",SHARED_CONFIG_FALLBACK_URL]\n    ];''',
'restore reliable config source order'
)

rep(
'''        const cfg=await fetchJsonWithTimeout(url);\n        applySharedSettings(cfg);\n        debugLog("CONFIG",`loaded from ${label}: draft ${draftId}, ${Object.keys(broadcastNames).length} names, ${absentUsernames.size} absent, ${autodraftUsernames.size} auto`);\n        updateSharedConfigSummary();\n        return true;''',
'''        const cfg=await fetchJsonWithTimeout(url);\n        applySharedSettings(cfg);\n\n        // Immediately after saving a new draft, Pages may still serve the old\n        // config for a few seconds. Keep the saving browser on the new draft for\n        // this one session; once the shared config catches up, discard the hint.\n        let pending="";\n        try{pending=String(sessionStorage.getItem(PENDING_DRAFT_SESSION_KEY)||"").trim()}catch(_){}\n        if(pending){\n          if(String(cfg?.draftId||"")===pending){\n            try{sessionStorage.removeItem(PENDING_DRAFT_SESSION_KEY)}catch(_){}\n          }else{\n            draftId=pending;\n            broadcastNames={};\n            absentUsernames=new Set();\n            autodraftUsernames=new Set();\n            debugLog("CONFIG",`using just-saved draft ${pending} while ${label} catches up`);\n          }\n        }\n\n        debugLog("CONFIG",`loaded from ${label}: draft ${draftId}, ${Object.keys(broadcastNames).length} names, ${absentUsernames.size} absent, ${autodraftUsernames.size} auto`);\n        updateSharedConfigSummary();\n        return true;''',
'pending draft override'
)

rep(
'''      if(reload){\n        // Raw/main updates before the Pages deployment, so reload after a short\n        // commit-settle delay rather than waiting for GitHub Pages to rebuild.\n        setTimeout(()=>location.reload(),1400);\n      }''',
'''      if(reload){\n        // Remember the just-saved draft only for this browser session. This is\n        // not a second configuration source; it simply bridges the Pages deploy\n        // delay after a successful shared-config commit.\n        try{sessionStorage.setItem(PENDING_DRAFT_SESSION_KEY,String(draftId))}catch(_){}\n        setTimeout(()=>location.reload(),700);\n      }''',
'stable post-save reload'
)


# -----------------------------------------------------------------------------
# Audio stability
# A pick should never sound like it is being booed. Warning crowd is a short cue
# at ~20 seconds, is not allowed to start immediately after a new pick, and is
# stopped instantly when a pick arrives.
# -----------------------------------------------------------------------------
rep(
'''  function fadeOutAudioGroup(group,duration=350){\n    cleanupFinishedClips();\n    activeClipAudios.filter(a=>a._dcGroup===group).forEach(a=>fadeOutAudio(a,duration));\n  }\n\n  function fadeOutAllAudio(duration=350){''',
'''  function fadeOutAudioGroup(group,duration=350){\n    cleanupFinishedClips();\n    activeClipAudios.filter(a=>a._dcGroup===group).forEach(a=>fadeOutAudio(a,duration));\n  }\n\n  function stopAudioGroup(group){\n    cleanupFinishedClips();\n    activeClipAudios.filter(a=>a._dcGroup===group).forEach(a=>{\n      try{a.pause();a.currentTime=0}catch(_){}\n    });\n    cleanupFinishedClips();\n  }\n\n  function fadeOutAllAudio(duration=350){''',
'hard stop audio group'
)

rep(
'''    // At 20 seconds the room starts getting restless. This is one crowd cue\n    // per turn, not a repeated sound on every render tick.\n    if(draft.status==="drafting" && secs<=20 && secs>0 && soundEnabled && !warningCrowdStarted){\n      warningCrowdStarted=true;\n      fadeOutAudioGroup("warning",220);\n      // Brief crowd impatience only: one low-level boo burst at 20 seconds,\n      // then quiet well before the final 10-second countdown.\n      playTags(["crowd","boo"],.26,1,"warning","warning-boo",2600);\n    }''',
'''    // A little crowd impatience at ~20 seconds, never a reaction to a pick.\n    // The turn-age guard protects against stale timer data briefly making a new\n    // turn appear to be inside the warning window.\n    const turnAgeMs=Math.max(0,Date.now()-turnStartedAt);\n    if(draft.status==="drafting" && secs<=20 && secs>10 && turnAgeMs>=7500 && soundEnabled && !warningCrowdStarted){\n      warningCrowdStarted=true;\n      fadeOutAudioGroup("warning",120);\n      playTags(["crowd","boo"],.24,1,"warning","warning-boo",2400);\n    }''',
'20 second warning guard'
)

rep(
'''        hidePressure();\n        playPickStinger();\n        fadeOutAudioGroup("warning",120);\n        warningCrowdStarted=false;''',
'''        hidePressure();\n        playPickStinger();\n        // A selection is never booed. Kill any tail of the 20-second warning\n        // immediately before the pick reveal/new turn is rendered.\n        stopAudioGroup("warning");\n        warningCrowdStarted=false;''',
'kill warning on pick'
)

p.write_text(s, encoding='utf-8')
print('stabilized config loading, post-save draft switching, and warning audio')
