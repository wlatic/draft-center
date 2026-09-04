from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')


def rep(old, new, label):
    global s
    if old not in s:
        raise SystemExit(f'{label}: target not found')
    s = s.replace(old, new, 1)

# The 20-second warning should be a brief bit of crowd impatience, not a long
# soundtrack that carries into the pick. One short boo burst, then quiet before
# the final 10-second countdown.
rep(
'''      // The warning is specifically booing. Rotate two verified CC0 boo clips
      // and fade them before the final countdown takes over.
      playTags(["crowd","boo"],.32,1,"warning","warning-boo",8500);''',
'''      // Brief crowd impatience only: one low-level boo burst at 20 seconds,
      // then quiet well before the final 10-second countdown.
      playTags(["crowd","boo"],.26,1,"warning","warning-boo",2600);''',
'brief 20-second boo'
)

# A pick is never itself a boo trigger. If the warning happens to still be
# audible when the pick arrives, get it out almost immediately while keeping a
# tiny fade so it does not click/pop.
rep(
'''        playPickStinger();
        fadeOutAudioGroup("warning",420);
        warningCrowdStarted=false;''',
'''        playPickStinger();
        fadeOutAudioGroup("warning",120);
        warningCrowdStarted=false;''',
'fast warning fade on pick'
)

p.write_text(s, encoding='utf-8')
print('restored restrained 20-second boo behavior')
