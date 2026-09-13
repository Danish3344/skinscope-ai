"""General educational information keyed by supported application labels."""

from __future__ import annotations

DISEASE_INFO: dict[str, dict[str, object]] = {
    "Atopic Dermatitis": {
        "description": "A chronic inflammatory skin condition often associated with itching and a recurring rash.",
        "symptoms": ["Itching", "Dry or scaly patches", "Red, brown, or purple rash", "Skin thickening after repeated scratching"],
        "precautions": ["Avoid known irritants", "Use moisturizer regularly", "Avoid scratching", "Consult a dermatologist for persistent flares"],
    },
    "Basal Cell Carcinoma": {
        "description": "A common type of skin cancer that often appears on sun-exposed skin and requires medical evaluation.",
        "symptoms": ["Pearly bump", "Non-healing sore", "Bleeding or crusting spot", "Shiny or scar-like patch"],
        "precautions": ["Seek professional diagnosis promptly", "Use sun protection", "Avoid tanning beds", "Monitor changing lesions"],
    },
    "Eczema": {
        "description": "A broad group of inflammatory skin conditions that can cause itchy, irritated, or cracked skin.",
        "symptoms": ["Itching", "Dryness", "Rash", "Cracking or oozing during flares"],
        "precautions": ["Moisturize frequently", "Avoid triggers", "Use gentle cleansers", "Get medical care for infection signs"],
    },
    "Melanoma": {
        "description": "A serious skin cancer that can develop from pigment-producing cells and needs urgent medical assessment.",
        "symptoms": ["Changing mole", "Irregular border", "Multiple colors", "Growing or bleeding lesion"],
        "precautions": ["Consult a dermatologist urgently", "Use sun protection", "Track ABCDE changes", "Do not self-treat suspicious lesions"],
    },
}


def get_disease_info(label: str) -> dict[str, object] | None:
    return DISEASE_INFO.get(label)
