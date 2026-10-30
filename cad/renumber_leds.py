#!/usr/bin/env python3
"""
Renumber the LED references on the main board to per-data-lane namespaces.

JLCPCB rejects refs with numeric portion above 2048. The current scheme
uses D1..D2560 across 8 chains, so any LED above D2048 would fail. This
script remaps:

    D1..D320     ->  DA1..DA320   (chain 1)
    D321..D640   ->  DB1..DB320   (chain 2)
    D641..D960   ->  DC1..DC320   (chain 3)
    D961..D1280  ->  DD1..DD320   (chain 4)
    D1281..D1600 ->  DE1..DE320   (chain 5)
    D1601..D1920 ->  DF1..DF320   (chain 6)
    D1921..D2240 ->  DG1..DG320   (chain 7)
    D2241..D2560 ->  DH1..DH320   (chain 8)

Each chain ends at 320, well under JLC's 2048 cap. The lane letter also
makes it obvious which data line an LED belongs to during debugging.

Also syncs D2561 -> TVS1 in the PCB, since the user's earlier rename in
the schematic didn't propagate.

Edits both .kicad_sch and .kicad_pcb in place. Updates:
  - (reference "D...")
  - (property "Reference" "D...")
  - Net-(D...-DOUT) and Net-(D...-DIN)

Run only after committing the current state -- this is destructive and
re-running after manual edits could conflict.
"""
import re
import sys


def new_led_ref(n):
    chain = (n - 1) // 320  # 0..7
    pos = (n - 1) % 320 + 1  # 1..320
    return f'D{chr(ord("A") + chain)}{pos}'


def build_mapping():
    m = {f'D{n}': new_led_ref(n) for n in range(1, 2561)}
    m['D2561'] = 'TVS1'  # sync stale PCB-side rename
    return m


def rename_in_file(path, mapping):
    with open(path) as f:
        content = f.read()
    before_len = len(content)

    # Build a single alternation of all old refs (longest first to avoid
    # any chance of "D1" matching inside "D10" -- the surrounding context
    # already prevents this, but belt-and-braces).
    keys_sorted = sorted(mapping.keys(), key=len, reverse=True)
    refs_alt = '|'.join(re.escape(k) for k in keys_sorted)

    patterns = [
        (re.compile(r'\(reference "(' + refs_alt + r')"\)'),
         lambda m: f'(reference "{mapping[m.group(1)]}")'),
        (re.compile(r'"Reference" "(' + refs_alt + r')"'),
         lambda m: f'"Reference" "{mapping[m.group(1)]}"'),
        (re.compile(r'Net-\((' + refs_alt + r')-DOUT\)'),
         lambda m: f'Net-({mapping[m.group(1)]}-DOUT)'),
        (re.compile(r'Net-\((' + refs_alt + r')-DIN\)'),
         lambda m: f'Net-({mapping[m.group(1)]}-DIN)'),
    ]

    counts = []
    for pat, repl in patterns:
        content, n = pat.subn(repl, content)
        counts.append(n)

    with open(path, 'w') as f:
        f.write(content)
    print(f'{path}: ref={counts[0]}  Reference={counts[1]}  '
          f'DOUT={counts[2]}  DIN={counts[3]}  size {before_len} -> {len(content)}')


def main(paths):
    mapping = build_mapping()
    print(f'mapping: {len(mapping)} refs '
          f'(D1->{mapping["D1"]}, D2560->{mapping["D2560"]}, D2561->{mapping["D2561"]})')
    for p in paths:
        rename_in_file(p, mapping)


if __name__ == '__main__':
    if not sys.argv[1:]:
        print('usage: renumber_leds.py <files...>')
        sys.exit(1)
    main(sys.argv[1:])
