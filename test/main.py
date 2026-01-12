
import sys
import unicodedata
import hashlib
import hmac

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
# Use 4-character sequences that won't collide with data encodings
ESC_2 = INVISIBLE[5] + INVISIBLE[5] + INVISIBLE[5] + INVISIBLE[0]
ESC_3 = INVISIBLE[5] + INVISIBLE[5] + INVISIBLE[5] + INVISIBLE[1]
ESC_4 = INVISIBLE[5] + INVISIBLE[5] + INVISIBLE[5] + INVISIBLE[2]

# -----------------------------
# CHARACTER SETS
# -----------------------------
SET_2 = " abcdefghijklmnopqrstuvwxyz012345678"
SET_3 = "9ABCDEFGHIJKLMNOPQRSTUVWXYZ.,!?@#$%^&*()-_=+[]{}<>/|~"

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
# TEXT TO SET_2 CONVERSION (for space optimization)
# -----------------------------
def text_to_set2(text: str) -> str:
    """
    Convert any text to SET_2-only representation for maximum space efficiency.
    Uses base-37 encoding of UTF-8 bytes.
    """
    if not text:
        return ""
    
    # Convert text to bytes
    text_bytes = text.encode('utf-8')
    
    # Convert bytes to a large integer
    num = int.from_bytes(text_bytes, 'big')
    
    # Convert to base-37 using SET_2 alphabet
    base = len(SET_2)
    if num == 0:
        return SET_2[0]
    
    result = []
    while num > 0:
        result.append(SET_2[num % base])
        num //= base
    
    # Reverse and add length prefix (also in base-37)
    encoded = ''.join(reversed(result))
    
    # Add length marker (original byte length in base-37)
    length_encoded = []
    length = len(text_bytes)
    if length == 0:
        length_encoded.append(SET_2[0])
    else:
        while length > 0:
            length_encoded.append(SET_2[length % base])
            length //= base
    
    # Format: <length>:<encoded_data>
    return ''.join(reversed(length_encoded)) + ':' + encoded

def set2_to_text(encoded: str) -> str:
    """
    Convert SET_2-only representation back to original text.
    """
    if not encoded:
        return ""
    
    # Split length and data
    if ':' not in encoded:
        return ""
    
    length_str, data_str = encoded.split(':', 1)
    
    # Decode length
    base = len(SET_2)
    length = 0
    for ch in length_str:
        length = length * base + SET_2.index(ch)
    
    # Decode data back to number
    num = 0
    for ch in data_str:
        num = num * base + SET_2.index(ch)
    
    # Convert number back to bytes
    if num == 0:
        text_bytes = b'\x00' * length
    else:
        text_bytes = num.to_bytes((num.bit_length() + 7) // 8, 'big')
    
    # Pad with zeros if needed
    if len(text_bytes) < length:
        text_bytes = b'\x00' * (length - len(text_bytes)) + text_bytes
    
    # Convert bytes back to text
    return text_bytes.decode('utf-8')

# -----------------------------
# FF1-LIKE FORMAT-PRESERVING ENCRYPTION
# -----------------------------
def ff1_encrypt_char(ch: str, key: str, index: int) -> str:
    """
    Simple format-preserving encryption for a single character.
    Uses HMAC-based key derivation and character set mapping.
    """
    if not key:
        return ch
    
    # Determine which character set this belongs to
    if ch in SET_2:
        charset = SET_2
        char_index = SET_2.index(ch)
    elif ch in SET_3:
        charset = SET_3
        char_index = SET_3.index(ch)
    else:
        # For byte mode (UTF-8), encrypt each byte
        return ch
    
    charset_size = len(charset)
    
    # Create a unique key for this position (position-based, not character-based)
    position_key = f"{key}:{index}".encode('utf-8')
    
    # Use HMAC to generate a pseudo-random shift (only based on position)
    h = hmac.new(position_key, b'', hashlib.sha256)
    shift = int.from_bytes(h.digest()[:4], 'big') % charset_size
    
    # Apply the shift (Caesar-like cipher within the character set)
    new_index = (char_index + shift) % charset_size
    return charset[new_index]

def ff1_decrypt_char(ch: str, key: str, index: int) -> str:
    """
    Decrypt a single character (reverse of ff1_encrypt_char).
    """
    if not key:
        return ch
    
    # Determine which character set this belongs to
    if ch in SET_2:
        charset = SET_2
        char_index = SET_2.index(ch)
    elif ch in SET_3:
        charset = SET_3
        char_index = SET_3.index(ch)
    else:
        # For byte mode (UTF-8), no decryption needed here
        return ch
    
    charset_size = len(charset)
    
    # Create the same unique key for this position
    position_key = f"{key}:{index}".encode('utf-8')
    
    # Calculate the same shift as in encryption
    h = hmac.new(position_key, b'', hashlib.sha256)
    shift = int.from_bytes(h.digest()[:4], 'big') % charset_size
    
    # Reverse the shift
    orig_index = (char_index - shift) % charset_size
    return charset[orig_index]

def ff1_encrypt(text: str, key: str) -> str:
    """Encrypt text using format-preserving encryption."""
    if not key:
        return text
    return ''.join(ff1_encrypt_char(ch, key, i) for i, ch in enumerate(text))

def ff1_decrypt(text: str, key: str) -> str:
    """Decrypt text using format-preserving encryption."""
    if not key:
        return text
    return ''.join(ff1_decrypt_char(ch, key, i) for i, ch in enumerate(text))

# -----------------------------
# ENCODE (HYBRID)
# -----------------------------
def encode(carrier: str, secret: str, key: str = "") -> str:
    # Apply FF1 encryption if key is provided
    encrypted_secret = ff1_encrypt(secret, key) if key else secret
    
    invis = []
    mode = None

    for ch in encrypted_secret:
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
def decode(stego: str, key: str = "") -> str:
    invis = [c for c in stego if c in INVISIBLE]
    out = []
    i = 0
    mode = None
    byte_buf = []

    while i < len(invis):
        # ALWAYS check for escape sequences first (need at least 4 characters)
        if i + 4 <= len(invis):
            quad = "".join(invis[i:i+4])

            if quad == ESC_2:
                # Flush byte buffer if coming from mode 4
                if byte_buf:
                    out.append(bytes(byte_buf).decode("utf-8"))
                    byte_buf = []
                mode = 2
                i += 4
                continue
            elif quad == ESC_3:
                # Flush byte buffer if coming from mode 4
                if byte_buf:
                    out.append(bytes(byte_buf).decode("utf-8"))
                    byte_buf = []
                mode = 3
                i += 4
                continue
            elif quad == ESC_4:
                # Flush byte buffer if coming from mode 4
                if byte_buf:
                    out.append(bytes(byte_buf).decode("utf-8"))
                    byte_buf = []
                mode = 4
                i += 4
                continue

        # Not an escape sequence, decode based on current mode
        if mode == 2:
            if i + 2 <= len(invis):
                pair = invis[i] + invis[i+1]
                out.append(DEC_2[pair])
                i += 2
            else:
                break

        elif mode == 3:
            if i + 3 <= len(invis):
                tri = invis[i] + invis[i+1] + invis[i+2]
                out.append(DEC_3[tri])
                i += 3
            else:
                break

        elif mode == 4:
            if i + 4 <= len(invis):
                quad = invis[i] + invis[i+1] + invis[i+2] + invis[i+3]
                byte_buf.append(DEC_4[quad])
                i += 4
            else:
                break

        else:
            break

    if byte_buf:
        out.append(bytes(byte_buf).decode("utf-8"))

    decrypted_text = "".join(out)
    # Apply FF1 decryption if key is provided
    return ff1_decrypt(decrypted_text, key) if key else decrypted_text

# -----------------------------
# CLI
# -----------------------------
if __name__ == "__main__":
    if "--encode" in sys.argv:
        real = input("Real text: ")
        hidden = input("Hidden text: ")
        key = input("Encryption key (optional, press Enter to skip): ").strip()

        out = encode(real, hidden, key)

        print("\nHuman view:")
        print(out)

        print("\nUnicode (computer) view:")
        print(out.encode("unicode_escape").decode())
    elif "--decode" in sys.argv:
        stego_text = input("Paste encoded text: ")
        key = input("Encryption key (optional, press Enter to skip): ").strip()
        print(decode(stego_text, key))
    else:
        print("Usage: ")
        print("--encode")
        print("--decode")
