# Japan buying standard / Osaka review — source and validation notes

Date: 2026-10-13 (Asia/Tokyo). Research session crossed midnight from October 12.
Primary deliverable: `tieu-chuan-mua-nha-nhat-va-review-osaka.html`.
Audience: product stakeholders (personal decision-maker); language Vietnamese.

## Scope and decisions

- User requested an independent ordinary Japan home-buying standard, comparison with the existing personalized Osaka standard, all documented.
- J01–J16 are an original operational due-diligence framework, not a national standard or a copy of a source handbook.
- Coverage: owner occupation, new/used, detached/condominium. Custom construction requires additional design/construction contracting work.
- Review target: `bo-tieu-chuan-mua-nha.html`, including its distinction between mandatory checks, asset value, appreciation factors, and secondary living preferences.
- The previous standard remains unchanged. SHA256 recorded before this work: `B39F2F5288982C0B3365BCFAC501D1A57803F92CD370428443AB4E6D763B0CDD`.
- Proposed Osaka v1.1 addendum appears in sections C–D of the new document. It is not silently substituted for the previous document or approved crawler settings.
- Latest confirmed cash: [số dư cá nhân đã ẩn], current balance, NOT a mandated untouched reserve. Preferred price 4,000–5,000万円; hold 10–20 years; both property types; permanent residency; no lender quote.
- No current affordability verdict, no invented income/debts/household needs, no forecast of appreciation, no property-level certification.
- Schooling, personal commute and amenities remain secondary only in the personalized standard; a user-confirmed minimum need remains a gate.
- No new crawl, database mutation, financial application or contact with external parties.

## Review findings

Keep: gating before ranking; ability to carry without appreciation; separate detached/condo due diligence; maintenance reserves; transaction comparables with adjustments; conditional rental fallback; no blind neighborhood-growth inference.

Material gaps: financing execution and 団信, counterparties and money-transfer verification, deposit/loan contingency mechanics, new-versus-used warranty scope, insurance residual losses, title funding shares/tax, and closing execution.

Refine: proposed financial thresholds need household calibration; age alone is not quality; sample count alone is not reliable valuation; road/frontage preferences are not legal rules; generic lifestyle criteria are household dependent.

General property selection standards and transaction legal rules are distinguished. “Hold / unknown” is not “pass.” No numerical total score that can offset a legal or financial failure.

## Primary sources consulted

Direct source links are in the HTML near factual claims. The following source descriptions are provenance notes, not independent legal interpretations.

1. RETIO, 不動産売買の手引 令和8年度版, June 2026. Confirmed official PDF title, transaction structure, contract termination topics and printed page 42 warranty distinctions. Used narrowly for important-explanation timing/conditional exits and scope of new-home basic-structure liability; original checklists are recommendations, not reproduced handbook text.
   https://www.retio.or.jp/wp-content/uploads/2026/06/R08%E4%B8%8D%E5%8B%95%E7%94%A3%E5%A3%B2%E8%B2%B7%E3%81%AE%E6%89%8B%E5%BC%95_%E4%BB%A4%E5%92%8C8%E5%B9%B4%E5%BA%A6%E7%89%88.pdf
2. MLIT, consumer real estate transaction notices. Role of transaction documents and actors, context for transaction stages.
   https://www.mlit.go.jp/totikensangyo/const/1_6_bf_000013.html
3. JHF loan simulation. Planning resource only; does not establish the report's proposed household ratios.
   https://www.jhf.go.jp/simulation_loan/
4. JHF 新機構団信 application and cautions. Health disclosure, insured-person scope and product-specific limits. No generalization to all lenders.
   https://www.jhf.go.jp/danshin_menu/shin-danshin/tetuduki.html
5. MLIT existing-home inspection. Explicitly recognizes limits; inspection does not guarantee absence of defects.
   https://www.mlit.go.jp/tochi_fudousan_kensetsugyo/const/tochi_fudousan_kensetsugyo_const_tk3_000001_00063.html
6. MLIT seismic provisions history, used for distinction between applicable standard and mere completion-year label.
   https://www.mlit.go.jp/common/001204021.pdf
7. Osaka-shi roads under building standards. Local lookup, not a nationwide proxy; numeric soft preferences in old standard are not statutory frontage rules.
   https://www.city.osaka.lg.jp/toshikeikaku/page/0000012309.html
8. MLIT condominium management certification. Supplementary evidence, not a substitute for current financial/maintenance records; no claim that future amendments are already effective.
   https://www.mlit.go.jp/jutakukentiku/house/keikakunintei.html
9. MOF earthquake insurance FAQ and system overview. Earthquake-caused fire/collapse not ordinary fire-insurance coverage; scope/caps must be read, no full-rebuild assumption.
   https://www.mof.go.jp/faq/financial_system/ei01.html
   https://www.mof.go.jp/policy/financial_system/earthquake_insurance/jisin.htm
10. MLIT energy standard explainer. April 2025 commencement-based new-building requirement, not a claim that all existing homes require retroactive compliance.
    https://www.mlit.go.jp/shoene-jutaku/
11. MLIT new-home purchase precautions. Financial security for defect liability, insurance/deposit arrangements; not a blanket warranty on all equipment.
    https://www.mlit.go.jp/jutakukentiku/jutaku-kentiku.files/kashitanpocorner/consumer/newly_house_purchase_attention.html
12. NTA No.4411, legal status April 1, 2026. Potential gift-tax issue if funding share differs from registered ownership share between spouses. No assumption that user has spouse/co-borrower.
    https://www.nta.go.jp/taxes/shiraberu/taxanswer/zoyo/4411.htm
13. CHORD service expansion / 住まいるダイヤル. Referral only; eligibility differs by service.
    https://www.chord.or.jp/expand/

Tokyo housing handbook portal returned 403 in this session; it is not used as evidence. The official RETIO PDF was fetched directly successfully. Third-party discovery pages and older NTA tax-limit examples were not relied on.

## Numerical definitions and checks

- 1万円 = 10,000 JPY; [số dư cá nhân đã ẩn] = [số dư cá nhân đã ẩn]. Confirmed cash is not down payment capacity.
- Historical proposal examples are labeled assistant proposals and linked to the previous standard: reserve 12 months, normal housing ratio 30%, stress warning 40%, income -20%, loan rate +2 percentage points, non-loan housing costs +30%, condo age 20, target 5 comparables / 12–24 months, road/frontage/station preferences.
- Stress illustration: 0.30 / (1 - 0.20) = 0.375 = 37.5%, holding housing costs fixed. It is not a calculation using user financial data.
- Payment stress must be applied to actual product repricing terms, not by simply increasing the original monthly payment by the rate delta.
- Financial ratios use household stable take-home income; not interchangeable with bank gross-income debt-service ratios.
- No standardized numerical score, probability or appreciation estimate created.

## Delivery and QA plan

- Standalone semantic HTML adapted from the prior report's skill-derived shell; no external fonts/styles/scripts, readable without JavaScript, light/dark media modes, print styling.
- Tables are exact qualitative mappings/checklists. No quantitative chart: there is no empirical series or comparable metric to encode. Therefore no chart payload or Recharts runtime is needed; no chart placeholder is present.
- All tables wrapped directly by `.table-scroll`; no `.wide` cards. Numeric evidence/proposals have accessible focusable source tooltips. Dates and criterion labels are document metadata, not analytical metrics.
- Verify section-role ordering, all J01–J16 criteria, unique IDs, internal and sibling file links, original-file hash, no placeholders or encoding corruption, no page overflow, no network dependency or browser errors. Inspect desktop/mobile screenshots and tooltip behavior.
- Record execution results in `japan-standard-review-qa.json` after QA; screenshots in the same report directory.

## Executed QA — passed

Command: `python -X utf8 verify_japan_standard.py` from the project directory, exit code 0.

- Four browser contexts passed: desktop light, desktop dark, mobile light, mobile dark with JavaScript disabled.
- Sixteen criteria, four wrapped tables, fourteen complete focusable source tooltips, one title, correct section-role order.
- No page-level horizontal overflow at 1440px or 390px; wide tables scroll inside their wrappers.
- All internal anchors and sibling-document links resolve; IDs are unique.
- No remote dependency requests and no browser page errors.
- Previous document SHA256 unchanged; stress arithmetic passed.
- Visually inspected desktop light/dark summary, desktop comparison table, mobile summary and mobile dark comparison table. Mobile tables retain horizontal scrolling for full row comparison.
- Initial invocation without UTF-8 completed browser assertions and file output, then failed printing Vietnamese JSON to Windows cp1252 stdout. Re-running in Python UTF-8 mode resolved this environment-only output failure without modifying the report.
- Machine-readable results: `japan-standard-review-qa.json`; screenshot files: `japan-review-*-top.png` and `japan-review-*-review.png`.

Validation boundary: rendering and document-structure tests do not validate a particular property's title, loan approval, physical safety or tax eligibility. The substantive review is a source-backed checklist review, not a professional transaction sign-off.
