// -----------------------------
// INVISIBLE ALPHABET
// -----------------------------
const INVISIBLE = [
  "\u200c", // 0
  "\u200d", // 1
  "\u2060", // 2
  "\u2061", // 3
  "\u2062", // 4
  "\u2063", // 5
];

const BASE = INVISIBLE.length;

// -----------------------------
// ESC MARKERS
// -----------------------------
// Use 4-character sequences that won't collide with data encodings
const ESC_2 = INVISIBLE[5] + INVISIBLE[5] + INVISIBLE[5] + INVISIBLE[0];
const ESC_3 = INVISIBLE[5] + INVISIBLE[5] + INVISIBLE[5] + INVISIBLE[1];
const ESC_4 = INVISIBLE[5] + INVISIBLE[5] + INVISIBLE[5] + INVISIBLE[2];

// -----------------------------
// CHARACTER SETS
// -----------------------------
const SET_2 = " abcdefghijklmnopqrstuvwxyz012345678";
const SET_3 = "9ABCDEFGHIJKLMNOPQRSTUVWXYZ.,!?@#$%^&*()-_=+[]{}<>/|~";

// -----------------------------
// MAP BUILDERS
// -----------------------------
const ENC_2 = {};
const DEC_2 = {};
const ENC_3 = {};
const DEC_3 = {};
const ENC_4 = {};
const DEC_4 = {};

// --- SET-2 (2 invisibles per char)
for (let i = 0; i < SET_2.length; i++) {
  const a = Math.floor(i / BASE);
  const b = i % BASE;
  const pair = INVISIBLE[a] + INVISIBLE[b];
  ENC_2[SET_2[i]] = pair;
  DEC_2[pair] = SET_2[i];
}

// --- SET-3 (3 invisibles per char)
for (let i = 0; i < SET_3.length; i++) {
  const a = Math.floor(i / (BASE * BASE));
  const rem = i % (BASE * BASE);
  const b = Math.floor(rem / BASE);
  const c = rem % BASE;
  const triple = INVISIBLE[a] + INVISIBLE[b] + INVISIBLE[c];
  ENC_3[SET_3[i]] = triple;
  DEC_3[triple] = SET_3[i];
}

// --- BYTE MODE (4 invisibles per byte)
for (let val = 0; val < 256; val++) {
  const a = Math.floor(val / (BASE ** 3));
  let rem = val % (BASE ** 3);
  const b = Math.floor(rem / (BASE ** 2));
  rem = rem % (BASE ** 2);
  const c = Math.floor(rem / BASE);
  const d = rem % BASE;
  const quad = INVISIBLE[a] + INVISIBLE[b] + INVISIBLE[c] + INVISIBLE[d];
  ENC_4[val] = quad;
  DEC_4[quad] = val;
}

// -----------------------------
// FF1-LIKE FORMAT-PRESERVING ENCRYPTION
// -----------------------------
async function hmacSHA256(key, message) {
  const encoder = new TextEncoder();
  const keyData = encoder.encode(key);
  const messageData = encoder.encode(message);
  
  const cryptoKey = await crypto.subtle.importKey(
    'raw',
    keyData,
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign']
  );
  
  const signature = await crypto.subtle.sign('HMAC', cryptoKey, messageData);
  return new Uint8Array(signature);
}

function ff1_encrypt_char(ch, key, index) {
  if (!key) return ch;
  
  // Determine which character set this belongs to
  let charset, char_index;
  if (SET_2.includes(ch)) {
    charset = SET_2;
    char_index = SET_2.indexOf(ch);
  } else if (SET_3.includes(ch)) {
    charset = SET_3;
    char_index = SET_3.indexOf(ch);
  } else {
    // For byte mode (UTF-8), no encryption here
    return ch;
  }
  
  const charset_size = charset.length;
  const position_key = `${key}:${index}`;
  
  // Create a deterministic pseudo-random shift using simple hash (position-based only)
  let hash = 0;
  for (let i = 0; i < position_key.length; i++) {
    hash = ((hash << 5) - hash) + position_key.charCodeAt(i);
    hash = hash & hash;
  }
  
  const shift = Math.abs(hash) % charset_size;
  const new_index = (char_index + shift) % charset_size;
  return charset[new_index];
}

function ff1_decrypt_char(ch, key, index) {
  if (!key) return ch;
  
  // Determine which character set this belongs to
  let charset, char_index;
  if (SET_2.includes(ch)) {
    charset = SET_2;
    char_index = SET_2.indexOf(ch);
  } else if (SET_3.includes(ch)) {
    charset = SET_3;
    char_index = SET_3.indexOf(ch);
  } else {
    // For byte mode (UTF-8), no decryption needed
    return ch;
  }
  
  const charset_size = charset.length;
  const position_key = `${key}:${index}`;
  
  // Calculate the same shift as in encryption
  let hash = 0;
  for (let i = 0; i < position_key.length; i++) {
    hash = ((hash << 5) - hash) + position_key.charCodeAt(i);
    hash = hash & hash;
  }
  
  const shift = Math.abs(hash) % charset_size;
  
  // Reverse the shift
  const orig_index = (char_index - shift + charset_size) % charset_size;
  return charset[orig_index];
}

function ff1_encrypt(text, key) {
  if (!key) return text;
  return Array.from(text).map((ch, i) => ff1_encrypt_char(ch, key, i)).join('');
}

function ff1_decrypt(text, key) {
  if (!key) return text;
  return Array.from(text).map((ch, i) => ff1_decrypt_char(ch, key, i)).join('');
}

// -----------------------------
// ENCODE (HYBRID)
// -----------------------------
function encode(carrier, secret, key = "") {
  // Apply FF1 encryption if key is provided
  const encrypted_secret = key ? ff1_encrypt(secret, key) : secret;
  
  let invis = [];
  let mode = null;

  for (let ch of encrypted_secret) {
    if (ch in ENC_2) {
      if (mode !== 2) { invis.push(ESC_2); mode = 2; }
      invis.push(ENC_2[ch]);
    }
    else if (ch in ENC_3) {
      if (mode !== 3) { invis.push(ESC_3); mode = 3; }
      invis.push(ENC_3[ch]);
    }
    else {
      if (mode !== 4) { invis.push(ESC_4); mode = 4; }
      const bytes = new TextEncoder().encode(ch);
      for (let b of bytes) {
        invis.push(ENC_4[b]);
      }
    }
  }

  let invis_stream = invis.join("");
  let out = [];
  let i = 0;

  for (let c of carrier) {
    out.push(c);
    if (i < invis_stream.length) {
      out.push(invis_stream.slice(i, i + 15)); // optional MAX_PER_GAP
      i += 15;
    }
  }

  if (i < invis_stream.length) {
    throw new Error("Carrier text too short");
  }

  return out.join("");
}

// -----------------------------
// DECODE (HYBRID)
// -----------------------------
function decode(stego, key = "") {
  const invis = Array.from(stego).filter(c => INVISIBLE.includes(c));
  let out = [];
  let i = 0;
  let mode = null;
  let byte_buf = [];

  while (i < invis.length) {
    // ALWAYS check for escape sequences first (need at least 4 characters)
    if (i + 4 <= invis.length) {
      const quad = invis.slice(i, i + 4).join("");

      if (quad === ESC_2) {
        // Flush byte buffer if coming from mode 4
        if (byte_buf.length) {
          out.push(new TextDecoder().decode(new Uint8Array(byte_buf)));
          byte_buf = [];
        }
        mode = 2;
        i += 4;
        continue;
      } else if (quad === ESC_3) {
        // Flush byte buffer if coming from mode 4
        if (byte_buf.length) {
          out.push(new TextDecoder().decode(new Uint8Array(byte_buf)));
          byte_buf = [];
        }
        mode = 3;
        i += 4;
        continue;
      } else if (quad === ESC_4) {
        // Flush byte buffer if coming from mode 4
        if (byte_buf.length) {
          out.push(new TextDecoder().decode(new Uint8Array(byte_buf)));
          byte_buf = [];
        }
        mode = 4;
        i += 4;
        continue;
      }
    }

    // Not an escape sequence, decode based on current mode
    if (mode === 2) {
      if (i + 2 <= invis.length) {
        const pair = invis[i] + invis[i + 1];
        out.push(DEC_2[pair]);
        i += 2;
      } else {
        break;
      }
    }
    else if (mode === 3) {
      if (i + 3 <= invis.length) {
        const triple = invis[i] + invis[i + 1] + invis[i + 2];
        out.push(DEC_3[triple]);
        i += 3;
      } else {
        break;
      }
    }
    else if (mode === 4) {
      if (i + 4 <= invis.length) {
        const quad = invis[i] + invis[i + 1] + invis[i + 2] + invis[i + 3];
        byte_buf.push(DEC_4[quad]);
        i += 4;
      } else {
        break;
      }
    }
    else break;
  }

  if (byte_buf.length) {
    out.push(new TextDecoder().decode(new Uint8Array(byte_buf)));
  }

  const decrypted_text = out.join("");
  // Apply FF1 decryption if key is provided
  return key ? ff1_decrypt(decrypted_text, key) : decrypted_text;
}

// -----------------------------
// Example usage in browser
// -----------------------------
/*
const carrier = "Hello world";
const secret = "abcdef XYZ 123!";
const encoded = encode(carrier, secret);
console.log("Encoded:", encoded);
console.log("Decoded:", decode(encoded));
*/
