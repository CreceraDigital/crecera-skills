# Hospitality-Specific Handling

When the site is a hotel, resort, restaurant group, or similar property — apply these additional checks alongside the standard workflow. These are the recurring traps in hospitality migrations.

---

## Accommodation / room pages

- **Thin page sprawl risk.** Individual room pages need substantial unique content (≥250–400 words, ideally with amenities, square footage, view, occupancy, distinctive features). Generic "spacious king room with modern amenities" copy across 12 room types is a thin-content content liability.
- **Required signals in copy:** city + property brand + "hotel"/"suite"/"room" + at least one distinguishing feature.
- **Image alt text** for room photos should include property name and room type — often missed in handoff.

## Restaurant / dining pages

- Often carry significant **non-branded keyword value** (e.g., "[city] italian restaurant", "[city] rooftop dining"). Protect these carefully during restructuring.
- Common mistake: collapsing 3–5 named restaurant pages into one `/dining` page. This sheds non-brand rankings and link equity.
- Each named restaurant needs its own page with: cuisine type, hours, menu link, location, reservations CTA.

## Location-specific terms

Local/hospitality SEO requires city + service-term coverage **in the visible copy**, not just meta tags. Audit for:
- City name in H1, intro paragraph, and at least one body section
- Neighborhood / district mentions where relevant
- Nearby landmark references for context
- Distance-from-airport / "in the heart of [district]" patterns

## Schema markup

Hospitality schema is a competitive advantage — verify it migrates. Required types depending on page:

| Page type | Schema |
|---|---|
| Property home | `Hotel` |
| Room pages | `HotelRoom` |
| Restaurant pages | `Restaurant` (`servesCuisine`, `menu`, `acceptsReservations`) |
| Event venue pages | `EventVenue` or `Place` |
| Specific events | `Event` |
| FAQ pages | `FAQPage` |
| Wedding venue pages | `Place` with appropriate amenities |

If the current site has these and the new build doesn't, flag it loudly. Schema migration is one of the highest-leverage pre-launch checks.

## Seasonal offers pages

- Offers pages need redirect planning **even if content changes annually** — the URL itself accumulates backlinks and search equity.
- Common mistake: deleting `/offers/summer-2024` on launch instead of redirecting to `/offers/summer-2025` (or to the parent `/offers` hub).
- Recommend the redirect chain in the migration plan: each year's offer → current year's equivalent → /offers parent if expired.

## Wedding / events content

- Often ranks for **high-intent queries** ("[city] wedding venue", "[city] private events"). These convert at very different rates than rooms — protect URL equity.
- Common mistake: burying wedding pages inside a generic `/gather` or `/celebrate` section without redirects from the legacy `/weddings` URL.
- Wedding inquiry forms typically have higher revenue-per-conversion than room bookings — Tier 1 priority even if traffic is modest.

## Meetings & events

- Corporate meeting and event pages serve a distinct ICP from leisure traffic. Don't merge them with leisure event pages.
- Floor plans, capacity charts, A/V capabilities need to migrate intact (often PDFs — verify these don't 404).

## Spa / wellness sections

- Common pattern: a property with one spa page in the current IA gets expanded to 6 wellness pages (spa, treatments, gym, pool, sauna, mindfulness). If the brand only has source content for 1–2 of these, the rest will launch thin.
- Recommend: build the section based on real available content + capacity to write 400+ unique words per page. If they can't, collapse to fewer pages.

---

## Hospitality migration headline check

Before signing off any hospitality migration, confirm:

- [ ] Every room type has unique copy with city + brand + room-type signals
- [ ] Every named restaurant has its own URL with non-brand keyword targets preserved
- [ ] Wedding / events URLs either preserved or redirected with explicit notes
- [ ] Schema (Hotel, HotelRoom, Restaurant, Event, FAQPage) migrates intact
- [ ] Seasonal offers redirect chain is documented
- [ ] City and neighborhood signals appear in visible copy, not just meta
- [ ] Meeting/event PDFs and floor plans return 200, not 404, on new URLs
