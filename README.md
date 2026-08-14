# ◈ HABIT TRACKER

An offline, single-file habit tracker for iPhone. Eighties synthwave: near-black
background, neon pink and cyan, glowing monospace text, purple horizon grid.

No frameworks, no build step, no network calls, no tracking. Everything lives in
`index.html` and your browser's local storage.

![icon](icon-180.png)

## Tabs

**LOG** — a scrollable 60-day strip so you can tick off today or backfill any
earlier day. Tap a habit to toggle it; the ring under each date shows that day's
completion. `EDIT` mode lets you rename, recolour, reorder and delete habits.

**GRAPHS** — daily completion percentage with a 7-day average overlay (drag on it
to scrub), a calendar heat map (tap any cell to jump straight to that day's log),
and a rolling per-habit sparkline for every habit.

**STATS** — perfect-day streak and all-time best, 7/30/all-time completion rates,
total checks, top habit; a per-habit table of current streak, best streak and
period rate; a day-of-week breakdown (filterable to one habit); and 7-day vs
30-day rolling averages against the all-time mean.

Range selector (30D / 90D / 1Y / ALL) drives both the graphs and the stats.

## Data

Stored under the local-storage key `habit-tracker.v1`, on your device only.

From the ⚙ menu:

- **Export CSV** — long format, one row per habit per day:
  `date,weekday,habit_id,habit_name,completed`
- **Copy CSV to clipboard** — for when iOS blocks the download
- **Backup / restore (JSON)** — full round-trip of your data
- **Load demo data** — ~150 days of plausible history, to see the graphs populated
- **Erase everything**

A habit counts from the earlier of its creation date and its first logged entry,
so backfilling into the past never drags your rates down.

> Local storage is cleared if you erase Safari website data. Take a JSON backup
> now and then.

## Deploy to GitHub Pages

```bash
gh repo create habit-tracker --public --source . --push
```

Then turn on Pages:

```bash
gh api -X POST repos/:owner/habit-tracker/pages -f source[branch]=main -f source[path]=/
```

Or in the browser: **Settings → Pages → Source: Deploy from a branch → main → /
(root)**. The site appears at `https://<user>.github.io/habit-tracker/` within a
minute or two.

## Add to Home Screen (iPhone)

1. Open the Pages URL in **Safari** (Chrome on iOS cannot install to the Home
   Screen).
2. Tap the **Share** button → **Add to Home Screen** → **Add**.
3. Launch it from the icon. It opens full-screen with no browser chrome —
   `apple-mobile-web-app-capable` and the black-translucent status bar do that,
   and the layout respects the notch and home indicator via `safe-area-inset`.

The icon is `icon-180.png`, referenced as `apple-touch-icon`. iOS applies its own
rounded-corner mask, so the artwork is deliberately full-bleed square.

> The Home Screen copy uses a **separate local-storage bucket** from Safari on
> some iOS versions. Log in the installed app, not in the Safari tab, or use a
> JSON backup to move data across.

## Regenerating the icon

`make_icon.py` draws the logo from scratch: a flat two-colour mark, solid mint
background with **HT** in solid purple, drawn as terminal/bitmap letterforms on a
24×24 cell grid with uniform square strokes. No glow, shadow, bevel or gradient.
Writes `icon-180.png`, `icon-192.png` and `icon-512.png`. Pure Python standard
library — no Pillow, no downloads.

```bash
python make_icon.py
```

Tweak `MINT` / `PURPLE` for the colours and `H_ROWS` / `T_ROWS` for the
letterforms — they are literal ASCII bitmaps, so editing them edits the glyphs.

## Running locally

```bash
python -m http.server 8731
```

Then open `http://localhost:8731/`. Opening `index.html` via `file://` works too,
but the manifest and icon resolve more reliably over HTTP.
