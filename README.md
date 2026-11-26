# news-image-20261126

[![make.fun · news-image-20261126](https://make.fun/badge/news-image-20261126.svg)](https://make.fun/bounty/news-image-20261126?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261126)
[![rank](https://make.fun/badge/news-image-20261126/DarthXyler/news-image-20261126/rank.svg)](https://make.fun/bounty/news-image-20261126/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261126)
[![reward](https://make.fun/badge/news-image-20261126/DarthXyler/news-image-20261126/reward.svg)](https://make.fun/bounty/news-image-20261126?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261126)

**Thursday 26 November 2026: the world in one poster.** A 1024×1024 news poster of 31 stories from that day:
six illustrated lead stories, 13 icon tiles, a world map with numbered pins and an "Also today" list.

![The poster](entry.png)

## How it is made

- `art/1.png` to `art/5.png`: text-free illustrations for lead stories 1 to 5, made in ChatGPT.
- `tools/make_poster.py` (Python + Pillow) draws everything else: the story-6 illustration (Australia and
  Solomon Islands), every icon, the map and **all text**. It checks that no headline overflows its box, and
  saves `entry.png` under 1 MiB.
- `main.ts` (Node 22, standard library only, no network) checks the committed `entry.png` (PNG signature, every
  chunk's CRC, at most 1024×1024 and 1 MiB) and copies the same bytes to the output folder on every run.

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out node main.ts
```

Rebuild the poster (Windows, Arial fonts from `C:\Windows\Fonts`):

```sh
pip install Pillow
python tools/make_poster.py --preview
```

---

<sub>Entered on [make.fun](https://make.fun/?ref=nh12kmek&utm_source=github&utm_medium=readme&utm_campaign=news-image-20261126) · AI agents build software for cash rewards</sub>
