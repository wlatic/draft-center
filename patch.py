from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')


def rep(old, new, label):
    global s
    if old not in s:
        raise SystemExit(f'{label}: target not found')
    s = s.replace(old, new, 1)


# Default to a TV-friendly palette with much stronger position separation.
# A device-local setting can switch back to the previous Sleeper-like colors.
rep(
'''  --qb:#ee9dca;\n  --rb:#55d1bb;\n  --wr:#58d0dc;\n  --te:#f0c266;\n  --k:#b6a2ed;\n  --def:#f5a45d;\n  --other:#a9c4d8;\n}\n*{box-sizing:border-box}''',
'''  /* High-contrast TV palette: positions should read instantly from across a room. */\n  --qb:#60a5fa;\n  --rb:#34d399;\n  --wr:#f59e0b;\n  --te:#a78bfa;\n  --k:#fde047;\n  --def:#f87171;\n  --other:#a9c4d8;\n}\nbody.sleeper-palette{\n  --qb:#ee9dca;\n  --rb:#55d1bb;\n  --wr:#58d0dc;\n  --te:#f0c266;\n  --k:#b6a2ed;\n  --def:#f5a45d;\n  --other:#a9c4d8;\n}\n*{box-sizing:border-box}''',
'tv palette css'
)


# Add a Display tab and device-local palette control.
rep(
'''    <button class="settings-tab" type="button" data-pane="peoplePane">People</button>\n    <button class="settings-tab" type="button" data-pane="audioPane">Audio</button>\n    <button class="settings-tab" type="button" data-pane="debugPane">Debug</button>''',
'''    <button class="settings-tab" type="button" data-pane="peoplePane">People</button>\n    <button class="settings-tab" type="button" data-pane="displayPane">Display</button>\n    <button class="settings-tab" type="button" data-pane="audioPane">Audio</button>\n    <button class="settings-tab" type="button" data-pane="debugPane">Debug</button>''',
'display settings tab'
)

rep(
'''  <section class="settings-pane" id="audioPane">''',
'''  <section class="settings-pane" id="displayPane">\n    <div class="settings-grid">\n      <label>Position colors\n        <select id="positionPalette">\n          <option value="tv" selected>High Contrast TV</option>\n          <option value="sleeper">Sleeper-style</option>\n        </select>\n      </label>\n      <div></div>\n    </div>\n    <div class="people-help">High Contrast TV separates RB green and WR amber so they remain obvious from across the room. This setting is saved only on this device/browser.</div>\n  </section>\n\n  <section class="settings-pane" id="audioPane">''',
'display settings pane'
)


# Device-local display state. High contrast is the default for new devices.
rep(
'''  let roastLevel = "spicy";\n  const roastMemory = new Map();''',
'''  let roastLevel = "spicy";\n  let positionPalette = "tv";\n  const roastMemory = new Map();''',
'palette state'
)

rep(
'''  const initials = s => String(s||"").trim().split(/\\s+/).filter(Boolean).map(x=>x[0]).join("").slice(0,2).toUpperCase() || "—";\n\n  function renderDebugLog(){''',
'''  const initials = s => String(s||"").trim().split(/\\s+/).filter(Boolean).map(x=>x[0]).join("").slice(0,2).toUpperCase() || "—";\n\n  function loadPositionPalette(){\n    try{\n      const saved=localStorage.getItem("draftcenterPositionPalette");\n      positionPalette=saved==="sleeper"?"sleeper":"tv";\n    }catch(_){positionPalette="tv"}\n    applyPositionPalette(false);\n  }\n\n  function applyPositionPalette(save=true){\n    const sleeper=positionPalette==="sleeper";\n    document.body.classList.toggle("sleeper-palette",sleeper);\n    const select=$("positionPalette");\n    if(select)select.value=positionPalette;\n    if(save){\n      try{localStorage.setItem("draftcenterPositionPalette",positionPalette)}catch(_){}\n      debugLog("DISPLAY",`position colors → ${sleeper?"Sleeper-style":"High Contrast TV"}`);\n    }\n  }\n\n  function renderDebugLog(){''',
palette functions'
)


# Keep settings UI in sync and apply changes immediately.
rep(
'''    $("roastLevel").value=roastLevel;\n    $("volumeInput").value=Math.round(masterVolume*100);''',
'''    $("roastLevel").value=roastLevel;\n    $("positionPalette").value=positionPalette;\n    $("volumeInput").value=Math.round(masterVolume*100);''',
'populate palette setting'
)

rep(
'''  $("volumeInput").addEventListener("input",e=>{\n    setMasterVolume(e.currentTarget.value);\n  });''',
'''  $("positionPalette").addEventListener("change",e=>{\n    positionPalette=e.currentTarget.value==="sleeper"?"sleeper":"tv";\n    applyPositionPalette(true);\n  });\n\n  $("volumeInput").addEventListener("input",e=>{\n    setMasterVolume(e.currentTarget.value);\n  });''',
palette setting listener'
)

rep(
'''  async function boot(){\n    // Shared league settings are loaded once per page load.''',
'''  async function boot(){\n    loadPositionPalette();\n    // Shared league settings are loaded once per page load.''',
'load palette on boot'
)

p.write_text(s, encoding='utf-8')
print('added TV high-contrast position palette with device-local Sleeper toggle')
