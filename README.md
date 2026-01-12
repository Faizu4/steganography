
Invisible Unicode Steganography System

This project implements a stream-based invisible steganography system using Unicode invisible characters. It allows you to hide secret text inside normal-looking text without changing its visible appearance.

This README explains the design philosophy, encoding model, capacity math, and common pitfalls, so the system is easy to reason about and extend.


---

1. Core Idea

Visible text = carrier

Hidden text = secret

Secret is encoded using Unicode invisible characters (zero-width / format chars)

Invisibles are injected between visible characters

The final output looks identical to the carrier


Important:

> The system treats invisible characters as one continuous stream, not per-letter chunks.



---

2. Invisible Character Sets

We use multiple invisible characters to encode data.

Example pool:

INVISIBLE = [
    "\u200c", "\u200d", "\u200e", "\u200f",
    "\u2060", "\u2061", "\u2062", "\u2063",
]

Are these safe?

They are Unicode format characters

Invisible in most editors and UIs

Generally preserved in UTF-8 text

⚠️ Some platforms (messengers, sanitizers) may strip them


Always test the carrier medium.


---

3. Character Sets & Encoding Cost

Each hidden character belongs to a set, which determines how many invisible characters are required to encode it.

Set	Characters	Cost

SET_2	a–z, 0–8	2 invisibles
SET_3	A–Z, punctuation	3 invisibles
SET_4	Unicode / emoji	4 invisibles


SET_2 = set("abcdefghijklmnopqrstuvwxyz012345678")
SET_3 = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ.,!?@#$%^&*()-_=+[]{}<>/|~")


---

4. ESC Marker (Very Important)

An ESC marker is a short invisible prefix added once at the start of the hidden stream.

Purpose:

Tells the decoder which encoding mode / table is used

Prevents ambiguity when decoding


Key rule:

ESC_OVERHEAD = 3  # invisibles



5. Design Guarantees

✔ Single ESC ✔ Stream-safe decoding ✔ Mixed character sets supported ✔ No per-gap dependency ✔ Accurate capacity estimation


---

6. Future Improvements


More accurate fitting invisibles

Utility function more good



---

Final Note

Do you believe what you see?

