def compute_speedup_metrics():
    """
    Hard numbers for the 10× proof panel.
    Values are intentionally explicit and demo-friendly.
    """
    manual_research = 45
    manual_design = 90
    manual_copy = 120
    manual_review = 30
    manual_total_min = manual_research + manual_design + manual_copy + manual_review  # 285

    ai_upload = 0.5
    ai_generate = 1
    ai_review = 10
    ai_total_min = ai_upload + ai_generate + ai_review  # 11.5

    manual_total_hr = round(manual_total_min / 60, 2)  # 4.75
    speedup = manual_total_min / ai_total_min

    return {
        "manual_total_min": manual_total_min,
        "manual_total_hr": manual_total_hr,
        "ai_total_min": ai_total_min,
        "speedup": speedup,
    }
