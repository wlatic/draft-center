from pathlib import Path

p=Path('index.html')
s=p.read_text(encoding='utf-8')

# Remove the chant-like protest sample entirely. It reads like a soccer crowd,
# especially when fired as the clock-expired reaction.
s=s.replace(',{"id":"crowd_protest","tags":["crowd","boo","jeer","protest","timeout"],"url":"https://raw.githubusercontent.com/Wh1teDuke/WilhelmSFX/master/Samples/271425__karymronda__protest02.wav"}', '')

# Never select protest/chant as a warning, timeout, or test reaction.
s=s.replace('["boo","protest","aww","gasp"]', '["boo","aww","gasp"]')
s=s.replace('family==="boo"?.82:family==="protest"?.72:.68', 'family==="boo"?.82:.68')
s=s.replace('family==="boo"?.34:family==="protest"?.30:.28', 'family==="boo"?.34:.28')

p.write_text(s,encoding='utf-8')
