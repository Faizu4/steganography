
import sys
import unicodedata

arg = sys.argv

# -----------------------------
# INVISIBLE ALPHABET
# -----------------------------
INVISIBLE = [
    "\u200c",  # 0
    "\u200d",  # 1
    "\u2060",  # 2
    "\u2061",  # 3
    "\u2062",  # 4
    "\u2063",  # 5
]

BASE = len(INVISIBLE)
MAX_PER_GAP = 15

# -----------------------------
# ESC MARKERS
# -----------------------------
ESC_2 = INVISIBLE[0] * 3
ESC_3 = INVISIBLE[5] * 3
ESC_4 = INVISIBLE[2] * 3

# -----------------------------
# CHARACTER SETS
# -----------------------------
SET_2 = " abcdefghijklmnopqrstuvwxyz012345678"
SET_3 = "ABCDEFGHIJKLMNOPQRSTUVWXYZ.,!?@#$%^&*()-_=+[]{}<>/|~"

# -----------------------------
# MAP BUILDERS
# -----------------------------
ENC_2, DEC_2 = {}, {}
ENC_3, DEC_3 = {}, {}
ENC_4, DEC_4 = {}, {}

# --- SET-2 (2 invisibles)
for i, ch in enumerate(SET_2):
    a, b = divmod(i, BASE)
    ENC_2[ch] = INVISIBLE[a] + INVISIBLE[b]
    DEC_2[INVISIBLE[a] + INVISIBLE[b]] = ch

# --- SET-3 (3 invisibles)
for i, ch in enumerate(SET_3):
    a = i // (BASE * BASE)
    rem = i % (BASE * BASE)
    b, c = divmod(rem, BASE)
    ENC_3[ch] = INVISIBLE[a] + INVISIBLE[b] + INVISIBLE[c]
    DEC_3[INVISIBLE[a] + INVISIBLE[b] + INVISIBLE[c]] = ch

# --- BYTE MODE (4 invisibles per byte)
for val in range(256):
    a = val // (BASE ** 3)
    rem = val % (BASE ** 3)
    b = rem // (BASE ** 2)
    rem %= BASE ** 2
    c = rem // BASE
    d = rem % BASE
    quad = INVISIBLE[a] + INVISIBLE[b] + INVISIBLE[c] + INVISIBLE[d]
    ENC_4[val] = quad
    DEC_4[quad] = val

# -----------------------------
# ENCODE (HYBRID)
# -----------------------------
def encode(carrier: str, secret: str) -> str:
    invis = []
    mode = None

    for ch in secret:
        if ch in ENC_2:
            if mode != 2:
                invis.append(ESC_2)
                mode = 2
            invis.append(ENC_2[ch])

        elif ch in ENC_3:
            if mode != 3:
                invis.append(ESC_3)
                mode = 3
            invis.append(ENC_3[ch])

        else:
            if mode != 4:
                invis.append(ESC_4)
                mode = 4
            for b in ch.encode("utf-8"):
                invis.append(ENC_4[b])

    invis_stream = "".join(invis)

    out, i = [], 0
    for c in carrier:
        out.append(c)
        if i < len(invis_stream):
            out.append(invis_stream[i:i+MAX_PER_GAP])
            i += MAX_PER_GAP

    if i < len(invis_stream):
        raise ValueError("Carrier text too short")

    return "".join(out)

# -----------------------------
# DECODE (HYBRID)
# -----------------------------
def decode(stego: str) -> str:
    invis = [c for c in stego if c in INVISIBLE]
    out = []
    i = 0
    mode = None
    byte_buf = []

    while i < len(invis):
        tri = "".join(invis[i:i+3])

        if tri == ESC_2:
            mode = 2
            i += 3
            continue
        if tri == ESC_3:
            mode = 3
            i += 3
            continue
        if tri == ESC_4:
            mode = 4
            i += 3
            continue

        if mode == 2:
            pair = invis[i] + invis[i+1]
            out.append(DEC_2[pair])
            i += 2

        elif mode == 3:
            tri = invis[i] + invis[i+1] + invis[i+2]
            out.append(DEC_3[tri])
            i += 3

        elif mode == 4:
            quad = invis[i] + invis[i+1] + invis[i+2] + invis[i+3]
            byte_buf.append(DEC_4[quad])
            i += 4

        else:
            break

    if byte_buf:
        out.append(bytes(byte_buf).decode("utf-8"))

    return "".join(out)

# -----------------------------
# CLI
# -----------------------------
if __name__ == "__main__":
    if "--encode" in sys.argv:
        real = input("Real text: ")
        hidden = input("Hidden text: ")

        out = encode(real, hidden)

        print("\nHuman view:")
        print(out)

        print("\nUnicode (computer) view:")
        print(out.encode("unicode_escape").decode())
    elif "--decode" in sys.argv:
        print(decode(input("Paste encoded text: ")))
    else:
        print("Usage: ")
        print("--encode")
        print("--decode")
