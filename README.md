# LumaRef

I liked ZeeRef and BuzzRef both and trying to merge their best features together using Gemini.

A whiteboard for images and markdown notes on an infinite canvas. Use
it to track a project over time, or as a mood board for reference
images and artist assets.

LumaRef is a personal fork of [ZeeRef](https://github.com/zackgomez/zeeref)
by zackgomez and [BuzzRef](https://github.com/kistf001/buzzref) by kistf001.

## Installation

### Prebuilt binaries (recommended)

Download from the [latest release](https://github.com/safalevent/lumaref/releases/latest):

### From source

Requires Python 3.12 and [uv](https://docs.astral.sh/uv/).

```
git clone https://github.com/safalevent/lumaref.git
cd lumaref
uv sync
uv run lumaref
```

## CLI

`lumaref-cli` controls a running LumaRef session over a local socket —
useful for shell scripting and for AI agents that need to drop images,
write notes, or read what's currently on the board. See
`lumaref-cli --help` for the full subcommand list.

## Credits
Original BuzzRef by Rebecca Breu
Large images, Markdown text items, CLI for scripting and AI agents by ZackGomez
Sketching feature (PR #150) by Cinderflame-Linear
Crop rectangle improvements (PR #115) by DarkDefender
Pytest flag fix (PR #117) by DarkDefender
Show filename feature, SSL/User-Agent improvements by g-rix
PureRef file format library by FyorDev (MIT License)

## License

GPLv3 — see [LICENSE](LICENSE).

Copyright (C) 2025-2026 Zack Gomez.
Original BeeRef copyright (C) 2021-2024 Rebecca Breu.
