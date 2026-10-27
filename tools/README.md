# tools

`gen_assets.py` builds the README pictures in `assets/brand/` (`header`, `domains`, `capabilities`, `loop`, `stack`, `cta`, `repo-*`), one `-dark` and one `-light` file each, from the design tokens in `.design/tokens/`.

```bash
npm run assets          # or: python3 tools/gen_assets.py
```

Standard library only. Colours and radii live in `.design/tokens/semantic.tokens.json`; change one, run the command, commit the SVGs.

`data/` holds what the generator embeds so nothing loads from an outside site:

- `glyphs.json`: Inter outlines and kerning, so the wordmark and headlines are drawn as paths and look the same everywhere.
- `icons.json`: brand icon paths for the stack.

Rebuild `data/` only when you change fonts or icons: `python3 tools/bake_data.py --fonts <inter-otf-dir> --npm <node_modules>` (needs `fonttools`, `uharfbuzz`, and `simple-icons` plus `devicon` from npm).

Licences: Inter is SIL OFL 1.1, simple-icons is CC0, devicon is MIT. Brand marks belong to their owners.
