import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
import pandas as pd

random.seed(7)

OUT = Path(__file__).parent / "heidi_events.csv"


def gen():
    now = datetime.now(timezone.utc)
    rows = []
    total_users = 2800

    for i in range(total_users):
        user_id = f"U{i:05d}"
        clinic_id = f"C{random.randint(1, 45):03d}"
        role = random.choice(["clinician", "admin"])

        t0 = now - timedelta(days=random.randint(2, 21), hours=random.randint(0, 23))

        # base events
        rows.append((user_id, clinic_id, role, "signup_completed", t0))
        rows.append((user_id, clinic_id, role, "email_verified", t0 + timedelta(minutes=random.randint(2, 30))))
        rows.append((user_id, clinic_id, role, "workspace_created", t0 + timedelta(minutes=random.randint(10, 90))))

        # Make 11% drop-off at consult_created within 48h (Heidi-native wedge)
        drop = random.random() < 0.11

        if not drop:
            consult_time = t0 + timedelta(hours=random.randint(1, 40))
            rows.append((user_id, clinic_id, role, "consult_created", consult_time))
            rows.append((user_id, clinic_id, role, "consult_completed", consult_time + timedelta(minutes=random.randint(10, 60))))
            # note finalized sometimes delayed
            if random.random() < 0.85:
                rows.append((user_id, clinic_id, role, "note_finalized", consult_time + timedelta(minutes=random.randint(15, 120))))
        else:
            # still some product activity but no consult
            if random.random() < 0.6:
                rows.append((user_id, clinic_id, role, "template_selected", t0 + timedelta(hours=random.randint(1, 20))))

        # follow-up events sometimes
        if random.random() < 0.25:
            due = t0 + timedelta(days=random.randint(3, 12))
            rows.append((user_id, clinic_id, role, "followup_due", due))
            if random.random() < 0.7:
                rows.append((user_id, clinic_id, role, "followup_booked", due + timedelta(days=random.randint(0, 9))))

        # ehr sync occasionally
        if random.random() < 0.18:
            rows.append((user_id, clinic_id, role, "ehr_sync_connected", t0 + timedelta(hours=random.randint(2, 72))))

    df = pd.DataFrame(rows, columns=["user_id", "clinic_id", "role", "event_name", "timestamp"])
    df["timestamp"] = df["timestamp"].astype("datetime64[ns, UTC]")
    df = df.sort_values(["user_id", "timestamp"]).reset_index(drop=True)
    df.to_csv(OUT, index=False)
    print("Wrote:", OUT, "rows:", len(df))


if __name__ == "__main__":
    gen()
