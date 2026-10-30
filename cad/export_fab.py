#!/usr/bin/env python3
"""
Fab outputs for led_bage: 6-layer Gerbers + drill (zipped for the upload form),
plus BOM and centroid for turnkey assembly.

  gerbers/               one Gerber per layer, PTH/NPTH Excellon, job file
  led_bage-gerbers.zip   the above
  led_bage-bom.csv       Designator, Qty, Manufacturer, Manufacturer Part Number,
                         Value, Footprint; one row per part, designators spelled out
  led_bage-pos.csv       KiCad centroid (Ref, Val, Package, PosX, PosY, Rot, Side), mm
  led_bage-bom-jlc.csv   JLCPCB BOM: Comment, Designator, Footprint, LCSC Part #
  led_bage-cpl-jlc.csv   JLCPCB CPL: Designator, Mid X, Mid Y, Layer, Rotation

The MPN is the symbol's "Part Number" field where set, else its Value (this
project keeps most MPNs in Value). The JLCPCB files map MPNs to LCSC parts and
correct placements for JLC's own part models (ADR 0004).

Run: python3 cad/export_fab.py [out_dir]   (default cad/fab), then python3 cad/test_board.py
"""
import csv
import math
import pathlib
import shutil
import subprocess
import sys
import tempfile
import textwrap

CAD = pathlib.Path(__file__).resolve().parent
PCB, SCH = CAD / "led_bage.kicad_pcb", CAD / "led_bage.kicad_sch"
LAYERS = ("F.Cu,In1.Cu,In2.Cu,In3.Cu,In4.Cu,B.Cu,F.Paste,B.Paste,"
          "F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts")

# LCSC part per MPN for JLCPCB assembly. Where JLC can't place the designed part,
# a stocked equivalent stands in.
LCSC = {
    "CL10B105KA8NNNC": "C29936",
    "0603YC104KAT2A": "C130268",
    "CL21A106KAYNNNE": "C15850",
    "CSH0605-101M1CT": "C19270701",  # not stocked: JBLM2101M016C058RTM, 100 uF 16 V, 6.3x5.8 mm
    "XL-1010RGBC-WS2812B": "C5349953",  # listed as XL-1010RGBC-2812B
    "5024430870": "C587927",  # JLC unticks it on upload (hard-to-place fee); tick it in the BOM step
    "B10PS-VH(LF)(SN)": "C158035",
    "RCT02330RFLF": "C25104",  # basic part 0402WGF3300TCE
    "RCT02100KFLF": "C25741",  # basic part 0402WGF1003TCE; C173682 has no placement model
    "RCT0210KFLF": "C25744",  # basic part 0402WGF1002TCE
    "SMBJ6.0CA": "C19077561",
    "SI7145DP-T1-GE3": "C144873",
    "SN74AHCT1G125DBVR": "C7484",
}
# JLC places its own model of each part. Where that model's zero angle or origin
# differs from the KiCad footprint's: degrees to add, and the offset (mm, footprint
# coordinates) from the KiCad origin to JLC's. Read off JLC's placement preview.
JLC_FIX = {
    "SOT-23-5_L3.0-W1.7-P0.95-LS2.8-BL": (-90, (0, 0)),
    "SON8_SI7135DP-T1-GE3_VIS-L": (-90, (0, 0)),
    "JST_VH_B10PS-VH_1x10_P3.96mm_Horizontal": (0, (4.5 * 3.96, 0)),  # KiCad: pin 1, JLC: mid pin row
    "Molex_CLIK-Mate_502443-0870_1x08-1MP_P2.00mm_Vertical": (180, (0, 0.175)),  # JLC: mid-pads
}
JLC_DESIGNATOR_CHARS = 2000  # per BOM cell; JLC states 2048 but rejected a file with cells of 2045-2048


def jlc_placement(row):
    """KiCad centroid row -> JLC (x, y, rotation). JLC reads bottom-side angles as seen from below."""
    turn, (dx, dy) = JLC_FIX.get(row["Package"], (0, (0, 0)))
    rot, bottom = float(row["Rot"]), row["Side"] == "bottom"
    a = math.radians(rot)
    dy = dy if bottom else -dy  # footprint y points down; flipping to the back mirrors it
    x = float(row["PosX"]) + dx * math.cos(a) - dy * math.sin(a)
    y = float(row["PosY"]) + dx * math.sin(a) + dy * math.cos(a)
    return x, y, ((180 - rot if bottom else rot) + turn) % 360


def kicad(*args):
    subprocess.run(["kicad-cli", *map(str, args)], check=True, capture_output=True)


def export(out):
    out = pathlib.Path(out)
    gerbers = out / "gerbers"
    shutil.rmtree(gerbers, ignore_errors=True)
    gerbers.mkdir(parents=True)
    kicad("pcb", "export", "gerbers", "--check-zones", "--subtract-soldermask",
          "-l", LAYERS, "-o", f"{gerbers}/", PCB)
    kicad("pcb", "export", "drill", "--format", "excellon", "-u", "mm",
          "--excellon-separate-th", "-o", f"{gerbers}/", PCB)
    shutil.make_archive(str(out / "led_bage-gerbers"), "zip", gerbers)

    kicad("pcb", "export", "pos", "--format", "csv", "--units", "mm", "--side", "both",
          "--exclude-dnp", "-o", out / "led_bage-pos.csv", PCB)

    with tempfile.TemporaryDirectory() as tmp:
        raw = pathlib.Path(tmp, "bom.csv")
        kicad("sch", "export", "bom", "--exclude-dnp", "--ref-range-delimiter", "",
              "--fields", "Reference,${QUANTITY},Manufacturer,Part Number,Value,Footprint",
              "--labels", "Reference,Qty,Manufacturer,Part Number,Value,Footprint",
              "--group-by", "Value,Footprint", "-o", raw, SCH)
        with open(raw, newline="") as f:
            rows = list(csv.DictReader(f))
    with open(out / "led_bage-bom.csv", "w", newline="") as f, \
         open(out / "led_bage-bom-jlc.csv", "w", newline="") as g:
        w, jlc = csv.writer(f), csv.writer(g)
        w.writerow(["Designator", "Qty", "Manufacturer", "Manufacturer Part Number", "Value", "Footprint"])
        jlc.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
        for r in rows:
            mpn, footprint = r["Part Number"] or r["Value"], r["Footprint"].split(":")[-1]
            w.writerow([r["Reference"], r["Qty"], r["Manufacturer"], mpn, r["Value"], footprint])
            for cell in textwrap.wrap(r["Reference"].replace(",", " "), JLC_DESIGNATOR_CHARS):
                jlc.writerow([mpn, cell.replace(" ", ","), footprint, LCSC[mpn]])

    with open(out / "led_bage-pos.csv", newline="") as f, \
         open(out / "led_bage-cpl-jlc.csv", "w", newline="") as g:
        jlc = csv.writer(g)
        jlc.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        for r in csv.DictReader(f):
            x, y, rot = jlc_placement(r)
            jlc.writerow([r["Ref"], f"{x:.4f}mm", f"{y:.4f}mm", r["Side"].title(), f"{rot:g}"])
    print(f"fab outputs written to {out}")


if __name__ == "__main__":
    export(sys.argv[1] if len(sys.argv) > 1 else CAD / "fab")
