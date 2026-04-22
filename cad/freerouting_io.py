#!/usr/bin/env python3
"""
Round-trip a KiCad PCB through Freerouting.

Usage:
    freerouting_io.py export <board.kicad_pcb>
        -> writes <board>.dsn next to the PCB
    freerouting_io.py import <board.kicad_pcb> <routed.ses>
        -> imports routed tracks from the .ses back into the PCB

Run Freerouting between the two steps, e.g.:
    java -jar freerouting.jar -de board.dsn -do board.ses
(download: https://github.com/freerouting/freerouting/releases)
"""
import sys
from pathlib import Path
import pcbnew


def export_dsn(pcb_path: Path) -> Path:
    dsn = pcb_path.with_suffix('.dsn')
    board = pcbnew.LoadBoard(str(pcb_path))
    if not pcbnew.ExportSpecctraDSN(board, str(dsn)):
        raise RuntimeError(f'DSN export failed for {pcb_path}')
    print(f'{pcb_path.name} -> {dsn.name}')
    return dsn


def import_ses(pcb_path: Path, ses_path: Path) -> None:
    board = pcbnew.LoadBoard(str(pcb_path))
    if not pcbnew.ImportSpecctraSES(board, str(ses_path)):
        raise RuntimeError(f'SES import failed for {ses_path}')
    board.Save(str(pcb_path))
    print(f'{ses_path.name} -> {pcb_path.name}')


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    mode = argv[0]
    if mode == 'export' and len(argv) == 2:
        export_dsn(Path(argv[1]))
    elif mode == 'import' and len(argv) == 3:
        import_ses(Path(argv[1]), Path(argv[2]))
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
