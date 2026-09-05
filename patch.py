from pathlib import Path

p = Path("index.html")
s = p.read_text(encoding="utf-8")


def rep(old, new, label):
    global s
    if old not in s:
        raise SystemExit(f"{label}: target not found")
    s = s.replace(old, new, 1)


rep(
"""  --qb:#ee9dca;
  --rb:#55d1bb;
  --wr:#58d0dc;
  --te:#f0c266;
  --k:#b6a2ed;
  --def:#f5a45d;
  --other:#a9c4d8;
}
*{box-sizing:border-box}""",
"""  /* High-contrast TV palette: positions should read instantly from across a room. */
  --qb:#60a5fa;
  --rb:#34d399;
  --wr:#f59e0b;
  --te:#a78bfa;
  --k:#fde047;
  --def:#f87171;
  --other:#a9c4d8;
}
body.sleeper-palette{
  --qb:#ee9dca;
  --rb:#55d1bb;
  --wr:#58d0dc;
  --te:#f0c266;
  --k:#b6a2ed;
  --def:#f5a45d;
  --other:#a9c4d8;
}
*{box-sizing:border-box}""",
"tv palette css",
)

rep(
"""    <button class="settings-tab" type="button" data-pane="peoplePane">People</button>
    <button class="settings-tab" type="button" data-pane="audioPane">Audio</button>
    <button class="settings-tab" type="button" data-pane="debugPane">Debug</button>""",
"""    <button class="settings-tab" type="button" data-pane="peoplePane">People</button>
    <button class="settings-tab" type="button" data-pane="displayPane">Display</button>
    <button class="settings-tab" type="button" data-pane="audioPane">Audio</button>
    <button class="settings-tab" type="button" data-pane="debugPane">Debug</button>""",
"display settings tab",
)

rep(
"""  <section class="settings-pane" id="audioPane">""",
"""  <section class="settings-pane" id="displayPane">
    <div class="settings-grid">
      <label>Position colors
        <select id="positionPalette">
          <option value="tv" selected>High Contrast TV</option>
          <option value="sleeper">Sleeper-style</option>
        </select>
      </label>
      <div></div>
    </div>
    <div class="people-help">High Contrast TV separates RB green and WR amber so they remain obvious from across the room. This setting is saved only on this device/browser.</div>
  </section>

  <section class="settings-pane" id="audioPane">""",
"display settings pane",
)

rep(
"""  let roastLevel = "spicy";
  const roastMemory = new Map();""",
"""  let roastLevel = "spicy";
  let positionPalette = "tv";
  const roastMemory = new Map();""",
"palette state",
)

rep(
"""  const initials = s => String(s||"").trim().split(/\\s+/).filter(Boolean).map(x=>x[0]).join("").slice(0,2).toUpperCase() || "—";

  function renderDebugLog(){""",
"""  const initials = s => String(s||"").trim().split(/\\s+/).filter(Boolean).map(x=>x[0]).join("").slice(0,2).toUpperCase() || "—";

  function loadPositionPalette(){
    try{
      const saved=localStorage.getItem("draftcenterPositionPalette");
      positionPalette=saved==="sleeper"?"sleeper":"tv";
    }catch(_){positionPalette="tv"}
    applyPositionPalette(false);
  }

  function applyPositionPalette(save=true){
    const sleeper=positionPalette==="sleeper";
    document.body.classList.toggle("sleeper-palette",sleeper);
    const select=$("positionPalette");
    if(select)select.value=positionPalette;
    if(save){
      try{localStorage.setItem("draftcenterPositionPalette",positionPalette)}catch(_){}
      debugLog("DISPLAY",`position colors → ${sleeper?"Sleeper-style":"High Contrast TV"}`);
    }
  }

  function renderDebugLog(){""",
"palette functions",
)

rep(
"""    $("roastLevel").value=roastLevel;
    $("volumeInput").value=Math.round(masterVolume*100);""",
"""    $("roastLevel").value=roastLevel;
    $("positionPalette").value=positionPalette;
    $("volumeInput").value=Math.round(masterVolume*100);""",
"populate palette setting",
)

rep(
"""  $("volumeInput").addEventListener("input",e=>{
    setMasterVolume(e.currentTarget.value);
  });""",
"""  $("positionPalette").addEventListener("change",e=>{
    positionPalette=e.currentTarget.value==="sleeper"?"sleeper":"tv";
    applyPositionPalette(true);
  });

  $("volumeInput").addEventListener("input",e=>{
    setMasterVolume(e.currentTarget.value);
  });""",
"palette setting listener",
)

rep(
"""  async function boot(){
    // Shared league settings are loaded once per page load.""",
"""  async function boot(){
    loadPositionPalette();
    // Shared league settings are loaded once per page load.""",
"load palette on boot",
)

p.write_text(s, encoding="utf-8")
print("added TV high-contrast position palette with device-local Sleeper toggle")
