# CENTS prebuilt merchandise sourcing

CENTS uses a $0 asset budget. This folder is reserved for selected, downloaded retail-product GLBs; do not commit models until their individual source and licence metadata are recorded.

## Approved source pool

- Food and drink models: https://2dto3d.app/free-3d-models/food
- Page 2 (canned goods, milk, yogurt, boxed drinks, generic cans): https://2dto3d.app/free-3d-models/food/2
- Page 3 (packaged bread, pastries, snack bars): https://2dto3d.app/free-3d-models/food/3
- Page 4 (cereal, boxed foods, canned foods): https://2dto3d.app/free-3d-models/food/4
- Original source dataset: https://huggingface.co/datasets/nvidia/simready-assets

The catalogue identifies food models as NVIDIA SimReady assets under CC BY 4.0. Attribution required: NVIDIA, from NVIDIA SimReady, CC BY 4.0. Include the licence link and disclose modifications.

## First-pass convenience-store assortment

| Fictional CENTS SKU | Source model candidate | Shelf department |
|---|---|---|
| Ember Cola | Keep existing custom asset | Cold drinks |
| ClearSpring Water | Bottled water (generic) | Cold drinks |
| Northline Citrus Fizz | Bottled drink / generic can | Cold drinks |
| Daybreak Iced Tea | Generic bottled drink | Cold drinks |
| QuickBite Cheese Crackers | Box cracker | Snacks |
| Saltline Potato Crisps | Generic packaged snack / bar form factor | Snacks |
| Pocket Treat Chocolate | Generic bar | Checkout impulse |
| Morning Loop Cereal | Boxed cereal | Pantry |
| Homestead Milk | Milk | Cold drinks |
| Pantry Tomato Soup | Can tomato soup | Pantry |
| Pantry Beans | Canned beans | Pantry |
| Corner Bakery Danish | Packaged bread danish | Grab-and-go |
| Corner Bakery Loaf | Packaged bread loaf | Pantry |
| Deli Fresh Pasta Salad | Keep existing custom asset | Grab-and-go |

This is a candidate list, not a claim that all files have already been downloaded or approved. Avoid beer/alcohol, supplements, medicines, and irrelevant bulk packs. Prefer generic/unbranded scans. Where a source model visibly carries a third-party mark, remove its texture artwork and apply a fictional CENTS label; do not ship a recognizable logo or claim endorsement.

## Import contract

Place selected GLBs in this folder and add one manifest record per asset with:
- exact source title and source URL
- source author and licence
- local filename and SHA-256
- fictional SKU name and department
- target display height in metres
- front-facing axis / orientation verified in Blender

Keep Ember Cola and pasta salad as the two custom exceptions. Do not replace them with scanned substitutes.
