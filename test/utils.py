ESC_OVERHEAD = 3
MAX_PER_GAP = 15

SET_2 = set("abcdefghijklmnopqrstuvwxyz012345678")
SET_3 = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ.,!?@#$%^&*()-_=+[]{}<>/|~")

def classify_char(ch):
    if ch in SET_2:
        return 2
    elif ch in SET_3:
        return 3
    else:
        return 4  # emoji / unicode / everything else

def max_secret_capacity(carrier_text: str, hidden_text: str | None = None):
    carrier_chars = len(carrier_text)
    total_slots = carrier_chars * MAX_PER_GAP

    # No hidden text → theoretical max only
    if not hidden_text:
        return {
            "carrier_chars": carrier_chars,
            "total_invisible_slots": total_slots,
            "esc_overhead_slots": 0,
            "max_2_set_chars": total_slots // 2,
            "max_3_set_chars": total_slots // 3,
            "max_4_set_chars": total_slots // 4,
            "max_ascii_chars": total_slots // 4,
            "max_emoji_chars": (total_slots // 4) // 4,
        }

    # Actual hidden text → accurate estimate
    esc_overhead = ESC_OVERHEAD
    usable_slots = max(0, total_slots - esc_overhead)

    needed_slots = 0
    for ch in hidden_text:
        needed_slots += classify_char(ch)

    fits = needed_slots <= usable_slots

    return {
        "carrier_chars": carrier_chars,
        "total_invisible_slots": total_slots,
        "esc_overhead_slots": esc_overhead,
        "usable_slots": usable_slots,
        "required_slots_for_hidden": needed_slots,
        "fits": fits,
        "remaining_slots": usable_slots - needed_slots if fits else 0,
    }# -----------------------------
# CLI
# -----------------------------
if __name__ == "__main__":
    text = input("Enter carrier text: ")
    hidden = input("Enter hidden text (optional for more accuracy): ")
    info = max_secret_capacity(text, hidden)

    for k, v in info.items():
        print(f"{k}: {v}")
