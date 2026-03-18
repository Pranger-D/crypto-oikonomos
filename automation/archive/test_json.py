import json
from pathlib import Path
p = Path("public/data/dashboard-data.json")
with open(p, "r", encoding="utf-8") as f:
    data = json.load(f)
with open("out.txt", "w", encoding="utf-8") as out:
    out.write("Last 7 priceData entries:\n")
    for item in data["priceData"][-7:]:
        out.write(json.dumps(item) + "\n")
