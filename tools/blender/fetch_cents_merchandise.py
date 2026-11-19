#!/usr/bin/env python3
"""Fetch a curated set of real scanned convenience-product GLBs for CENTS.

Source: CodePawl's web-ready Google Scanned Objects GLB repackaging.
Original scans: Google Research / Google LLC, CC BY 4.0.
All downloaded package textures are removed by the Blender importer and replaced
with fictional CENTS labels; only the scanned product geometry is retained.
"""
import json
import os
import re
import sys
import urllib.request

BASE = "https://huggingface.co/datasets/codepawl/scanned-objects-glb/resolve/main"
META_URL = BASE + "/metadata.jsonl?download=true"

# A convenience-store assortment, not a general grocery or kitchen assortment.
TARGETS = [
    ("chips", "Saltline Potato Crisps", "snacks", 0),
    ("cracker", "QuickBite Cheese Crackers", "snacks", 1),
    ("cereal", "Morning Loop Cereal", "pantry", 2),
    ("bread|danish|pastry|cake", "Corner Bakery Pastry", "bakery", 3),
    ("candy|chocolate|bar", "Pocket Treat Chocolate", "checkout", 4),
    ("water", "ClearSpring Water", "cold-drinks", 0),
    ("soda|cola|sparkling", "Northline Citrus Fizz", "cold-drinks", 1),
    ("tea|juice|drink", "Daybreak Iced Tea", "cold-drinks", 2),
    ("soup", "Pantry Tomato Soup", "pantry", 3),
    ("bean", "Pantry Baked Beans", "pantry", 4),
    ("milk", "Homestead Milk", "cold-drinks", 0),
]
EXCLUDE = re.compile(r"beer|wine|whisky|whiskey|vodka|gin|rum|tequila|champagne|alcohol|supplement|vitamin|protein|medicine|drug|cleaner|detergent|shampoo|soap", re.I)
FOOD_CATEGORIES = {"food and drink", "food", "bottles and cups", "bottles and cans and cups"}

def fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": "CENTS-asset-builder/1.0"})
    with urllib.request.urlopen(request, timeout=90) as response:
        return response.read()

def main():
    output = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "build/merchandise")
    models_dir = os.path.join(output, "models")
    os.makedirs(models_dir, exist_ok=True)
    raw = fetch(META_URL).decode("utf-8")
    rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
    candidates = []
    for row in rows:
        name = str(row.get("name", ""))
        category = str(row.get("category", "")).strip().lower()
        if category not in FOOD_CATEGORIES or EXCLUDE.search(name):
            continue
        if not row.get("id"):
            continue
        candidates.append(row)

    selected = []
    used = set()
    for pattern, label, department, palette in TARGETS:
        regex = re.compile(pattern, re.I)
        matches = [r for r in candidates if regex.search(str(r.get("name", ""))) and r.get("id") not in used]
        if not matches:
            continue
        # Prefer compact packaged goods over large platters or loose produce.
        matches.sort(key=lambda r: (int(r.get("pack_bytes") or 9999999), str(r.get("name", ""))))
        row = matches[0]
        used.add(row["id"])
        selected.append({
            "id": row["id"], "source_name": row.get("name", ""),
            "label": label, "department": department, "palette": palette,
            "source": row.get("source") or "Google Scanned Objects",
            "license": row.get("license") or "CC-BY-4.0",
            "file": row.get("file") or ("objects/{0}/{0}.glb".format(row["id"])),
        })

    if len(selected) < 6:
        raise RuntimeError("Only {0} suitable food/drink scans matched; refusing to build an empty or irrelevant assortment. Candidate categories: {1}".format(
            len(selected), sorted({str(r.get("category")) for r in rows})))

    # Preserve the exact two authored SKUs. Replace the other five generated placeholder
    # product families with scanned geometry, laid out in the same existing shelf slots.
    manifest_products = []
    shelf_levels = (0.462, 0.952, 1.442)
    gondolas = (-2.35, 2.35)
    replacement = [p for p in selected if p["department"] != "cold-drinks"] or selected
    for gondola_index, gx in enumerate(gondolas):
        for row_index, shelf_z in enumerate(shelf_levels):
            for face in (-1, 1):
                for item in range(9):
                    kind = (item + row_index * 2 + gondola_index * 3) % 7
                    if kind in (0, 6):
                        continue
                    y = -2.55 + item * 0.64
                    x = gx + face * 0.34
                    if kind == 1:
                        pool = [p for p in selected if p["department"] == "cold-drinks"] or selected
                        height = 0.30
                    elif kind == 2:
                        pool = [p for p in selected if p["department"] in ("pantry", "cold-drinks")] or selected
                        height = 0.28
                    elif kind == 3:
                        pool = [p for p in selected if p["department"] in ("cold-drinks", "pantry")] or selected
                        height = 0.30
                    elif kind == 4:
                        pool = [p for p in selected if p["department"] in ("snacks", "checkout")] or selected
                        height = 0.31
                    else:
                        pool = [p for p in selected if p["department"] in ("checkout", "snacks")] or selected
                        height = 0.16
                    product = pool[(item + row_index + gondola_index) % len(pool)]
                    yaw = 0.0 if face > 0 else 3.141592653589793
                    manifest_products.append({
                        "file": product["id"] + ".glb",
                        "sku": product["label"].upper().replace(" ", "-"),
                        "label": product["label"], "position": [x, y, shelf_z],
                        "height": height, "yaw": yaw, "palette": product["palette"],
                        "department": product["department"],
                        "source_name": product["source_name"],
                        "source_url": "https://huggingface.co/datasets/codepawl/scanned-objects-glb",
                        "license": product["license"],
                    })

    for product in selected:
        target = os.path.join(models_dir, product["id"] + ".glb")
        if not os.path.isfile(target):
            data = fetch(BASE + "/" + product["file"].lstrip("/") + "?download=true")
            with open(target, "wb") as handle:
                handle.write(data)
        if os.path.getsize(target) < 4096:
            raise RuntimeError("Downloaded GLB is unexpectedly small: " + target)

    manifest = {
        "source": "Google Scanned Objects, Copyright 2020 Google LLC",
        "license": "CC BY 4.0",
        "attribution": "Google Research, Google Scanned Objects (2020), CC BY 4.0. Models repackaged by CodePawl as GLB. Product geometry retained; source packaging artwork/textures stripped and replaced with fictional CENTS labels.",
        "products": manifest_products,
        "source_models": selected,
    }
    with open(os.path.join(output, "manifest.json"), "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)
        handle.write("\n")
    print("CURATED_SOURCE_MODELS={0}".format(len(selected)))
    print("PLACED_MERCHANDISE_INSTANCES={0}".format(len(manifest_products)))
    for product in selected:
        print("SOURCE_MODEL={0} | CENTS_LABEL={1}".format(product["source_name"], product["label"]))

if __name__ == "__main__":
    main()
