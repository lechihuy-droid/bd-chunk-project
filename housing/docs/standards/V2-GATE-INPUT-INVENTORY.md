# v2 Gate Input Inventory

**Prepared:** 2026-11-03 (processing/inventory date, JST)  
**Dataset:** `ver2.0-20261102` (catalog observation date: 2026-11-02 JST)  
**Purpose:** Read-only inventory for planning implementation against [HOUSING-GATES-v1.0.md](HOUSING-GATES-v1.0.md). This is not a gate run or a property assessment.

## Inventory

`catalog/all-listings.csv` has **11,463 URL rows** and fields: `url`, `category`, `listing_level`, `title`, `price_jpy`, `price_raw`, `address`, `ward`, `land_m2`, `building_m2`, `unit_m2`, `layout`, `built_year`, `completion_raw`, `station_raw`, `preferred_budget`, `project_range_overlap`, `observed_at`. Categories: used condominium **7,739**, used house **2,750**, new house **802**, new condominium **172**. These are listing URLs, not confirmed unique properties.

`catalog/preferred-exact.csv` contains **1,754** rows: used condominium **1,162**, used house **329**, new house **263**, new condominium **0**. New-condominium project/range offers are separated in `catalog/projects.csv` (**309** rows: 160 new condominium, 149 new house); they are not exact-unit candidates. The finalized public preferred files contain **1,751 active exact listings**, **2 not-found**, and **1 unverified**. The public all-listings file has 11,463 rows and adds `availability`, `availability_reason`, and `availability_checked_at`; most rows were not individually availability-checked. A missing/expired listing is not proof of sale.

Catalog coverage reports **90 discovered routes** and **6 unresolved routes**, all `new_condo` with `route_not_discovered` and zero pages/cards: Higashinari, Ikuno, Minato, Naniwa, Nishinari, and Taisho wards. This is unknown coverage, not zero inventory. The catalog crawl completed on Nov 2, while this inventory was processed Nov 3; the dataset label is not a Nov 3 refresh.

The run has `crawl/detail-summary.json` with **40** successful detail extractions. Available extracted claim keys are `completion`, `coverage_far`, `energy`, `handover`, `insulation`, `lease_fee`, `management_fee`, `management_initial_fund`, `renovation`, `repair_fee`, `repair_initial_fund`, `rights`, `road`, `sale_units`, `setback`, `structure`, `total_units`, `utility_estimate`, and `zoning`. They are advertised claims parsed from listing pages; they do not establish legal, engineering, or transactional facts. Acquisition records also preserve source timestamps and cache references/hashes for review. Full cache/source content is not part of the public preferred CSV input.

The published list’s browser star key is `osaka-housing:stars:v1`; it stores listing URL strings in that browser’s local storage. It is user-interface state, not a gate evidence source or a project-wide record.

## Mapping to the five gates

| Gate | Existing inputs | Gap / interpretation for implementation |
|---|---|---|
| **G1 — scope and need** | URL, category/listing level, asking price (raw and parsed), address/ward, title, layout, area, completion/build year, station text, project overlap, observation and availability timestamps/status. | These support initial scope triage and identifying project/range rows. Advertisements alone do not verify occupancy/use, handover, full address, property identity, or configured buyer needs (including commute and household requirements). Missing evidence stays review/queue; do not infer PASS/FAIL. |
| **G2 — purchase/holding feasibility** | Listing price, advertised management/repair fees and initial funds, rights/road/setback/zoning/structure claims where present in the 40-detail sample. | Requires additional evidence and reviewer work for buyer-specific affordability/financing and property-specific rights, access, technical, hazard, and management obligations. Private buyer review is out of scope for this public inventory; no private values are reproduced here. |
| **G3 — asset and purchase quality** | Asking price, advertised size/age/layout, and some detail claims; the catalog may support candidate grouping and later comparable research. | Requires comparable transaction/offer evidence, total ownership/exit scenarios, condition/maintenance evidence, demand and resale analysis. Current parsed ads do not establish value, condition, or an investment conclusion. |
| **G4 — prioritization** | Public listing attributes can serve as descriptive inputs after G1–G3 evidence is modeled. | No gate-approved weights, evidence-backed scores, or coverage-qualified ranking exist in this inventory. Do not score or rank from the catalog alone. |
| **G5 — transaction decision** | No transaction dossier is inventoried in the public preferred listing data. | Requires current property, seller, financing, inspection, title/contract and professional review evidence. This public inventory cannot assess or expose private transaction/buyer records. |

## Reproduction

From the project root, this read-only Python command reproduces the CSV row counts and category counts above (using only the catalog/public CSVs):

```powershell
@'
import csv, collections, pathlib
root = pathlib.Path("output/ver2.0-20261102")
for name in ("catalog/all-listings.csv", "catalog/preferred-exact.csv", "public/preferred-exact.csv", "public/preferred-unverified.csv"):
    with (root / name).open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    print(name, "rows=", len(rows), "categories=", dict(collections.Counter(r["category"] for r in rows)))
'@ | python -
```

No crawl, HTTP request, source-data edit, or gate execution was performed to prepare this inventory.
