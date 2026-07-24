# ramen-pareto

Pareto frontier of ramen: taste (x, higher is better) vs. ease of access
(y, lower is better — e.g. wait time/reservation hassle, on a 1-10 scale
you assign yourself).

## Update the frontier

1. Edit `data/ramen.json` — add/change entries:
   ```json
   { "name": "...", "taste": 0-10, "ease_of_access": 0-10 }
   ```
2. Regenerate: `python3 scripts/frontier.py`
3. Commit. `git log -p output/frontier.svg` / `data/ramen.json` is the
   history of how the frontier has shifted.

## Export

`output/frontier.svg` is self-contained (own dark background, inline
styles, no JS) — copy it directly into another site, e.g.:

```html
<img src="frontier.svg" alt="ramen pareto frontier" width="720">
```

or inline the `<svg>` markup for it to scale with the page.
