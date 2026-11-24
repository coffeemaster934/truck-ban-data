# Data zákazů jízdy nákladních vozidel

`public_holidays` is a calendar reference only. A public holiday must never be
converted automatically into a truck-driving ban.

`holiday_bans` is reserved for individually reviewed records that include
`ban: true`, `verified: true`, `scope: "national"`, and an HTTPS `source_url`
to the applicable legal or transport-authority source. Regional or road-specific
restrictions must not be published as nationwide bans.

Add verified holiday records to `VERIFIED_HOLIDAY_BANS` and Poland's annual
summer schedules to `VERIFIED_POLISH_SUMMER_BANS` in `update_bans.py`. Use the
applicable year's official publication and include the required source metadata.
Do not edit generated `bans.json` directly or infer future dates by repeating a
previous year's period.

The app also requires its checked local calculator to confirm a holiday ban
before feed details can affect the result.

Do not add generic `standard_weekend_ban`, `summer_ban`, or `night_ban` fields
from unreviewed country metadata. Recurring restrictions are maintained in the
app's checked rules; the feed may carry a future annual schedule only when it
has been verified from that year's national source.
