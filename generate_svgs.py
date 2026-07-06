#!/usr/bin/env python3
"""
Generate the README project rows as individual SVG files under rows/ and
assemble the README markdown that stitches them together.

This is invoked by render.py on regular (non-special-template) days: it writes
rows/*.svg (+ rows/mobile/*.svg) and returns the README body via generate().

Each project is rendered as its own SVG (HTML inside a <foreignObject>) so that
it can be wrapped in its own link. The row images are embedded as <img> in the
README, and GitHub serves them as static images, so:
  * every asset (icons) must be inlined as a base64 data URI, and
  * links inside a row are NOT clickable -- the whole row is wrapped in an <a>
    in the assembled README instead.

Responsive: an <img> shows a fixed-width canvas scaled to fit, so a wide canvas
makes text tiny on narrow screens. Each row is therefore rendered at several
widths (DESKTOP / MEDIUM / SMALL / MOBILE, with smaller icons and reflowed text
as they narrow), and the README uses <picture> media queries to pick the variant
whose canvas is closest to the viewport (breakpoints at 500 / 750 / 1000px).

Icons are read from assets/icons/ (96x96 lossless WebP, pre-resized so this
script needs only the Python standard library). If you replace the source art,
refresh the 96px icons with ImageMagick, e.g.:

    magick desktop-plus.png -resize 96x96 -strip -define webp:lossless=true assets/icons/desktop-plus.webp

Run standalone to regenerate the SVGs:  python3 generate_svgs.py
"""

import base64
import math
import os
from collections import namedtuple

ROOT = os.path.dirname(os.path.realpath(__file__))
ASSETS = os.path.join(ROOT, "assets")
ICONS = os.path.join(ASSETS, "icons")
ROWS_DIR = os.path.join(ROOT, "rows")


def b64_webp(name):
    with open(os.path.join(ICONS, name), "rb") as f:
        return "data:image/webp;base64," + base64.b64encode(f.read()).decode()


def b64_svg(name):
    with open(os.path.join(ICONS, name), "rb") as f:
        return "data:image/svg+xml;base64," + base64.b64encode(f.read()).decode()


desktopPlus = b64_webp("desktop-plus.webp")
chip = b64_webp("generic-microchip.webp")
terminal = b64_webp("generic-terminal.webp")
discord = b64_svg("discord-audio-stream.svg")


# A rendering profile. `width` is the SVG canvas width; `icon`/`gap` size the
# logo and its spacing; `desc_cpl`/`sub_cpl` are the (deliberately conservative)
# chars-per-line estimates used to guess how many lines text wraps to.
Profile = namedtuple("Profile", "name width icon gap desc_cpl sub_cpl")

# One canvas width per viewport band so the image never has to scale far from
# 1:1 (which is what shrinks the text). DESKTOP is the default (widest); the
# others are picked by <picture> media queries below their max-width.
DESKTOP = Profile("desktop", 880, 52, 18, 88, 80)
MEDIUM = Profile("medium", 760, 48, 18, 75, 68)
SMALL = Profile("small", 600, 44, 16, 59, 53)
MOBILE = Profile("mobile", 400, 40, 14, 38, 34)

# Responsive variants, smallest max-width first (the browser picks the first
# matching <source>). DESKTOP is the fallback <img>, so it is not listed here.
VARIANTS = [
    (MOBILE, "(max-width: 550px)"),
    (SMALL, "(max-width: 900px)"),
    (MEDIUM, "(max-width: 1200px)"),
]


STYLE_TEMPLATE = """
      * { margin: 0; padding: 0; box-sizing: border-box; text-decoration: none; list-style: none; }
      .body {
        --text: #f0f6fc;
        --muted: #dce0e3;
        --accent: #58a6ff;
        --accent-3: #56d364;
        color: var(--text);
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", Helvetica, Arial, sans-serif;
        font-size: 15px;
        line-height: 1.6;
        padding: 12px 16px;
        animation: rise 0.5s cubic-bezier(0.2, 0.8, 0.2, 1) both;
      }
      .project { display: flex; align-items: flex-start; gap: __GAP__px; }
      .icon { width: __ICON__px; height: __ICON__px; flex-shrink: 0; object-fit: contain; margin-top: 2px; }
      .content { flex: 1; min-width: 0; }
      h2 { font-size: 22px; font-weight: 700; color: var(--text); }
      .name { font-weight: 700; font-size: 16px; color: var(--accent); }
      .desc { color: var(--muted); margin-top: 2px; }
      em { color: var(--text); font-style: italic; }
      .subrow { padding-left: __SUBROW__px; }
      .sub { padding-left: 4px; }
      .sub li { color: var(--muted); padding-left: 16px; position: relative; }
      .sub li::before {
        content: ""; position: absolute; left: 2px; top: 11px;
        width: 5px; height: 5px; border-radius: 50%; background: var(--accent-3);
      }
      .sub a { color: var(--accent); font-weight: 500; }
      @keyframes rise { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
      @media (prefers-color-scheme: light) {
        .body { --text: #1f2328; --muted: #59636e; --accent: #0969da; --accent-3: #1a7f37; }
      }
      @media (prefers-reduced-motion) { .body { animation: none; } }
"""

TITLE_H = 25.6  # rendered height of the .name line (16px * 1.6)
LINE_H = 24     # rendered height of one body line (15px * 1.6)


def style(p):
    return (
        STYLE_TEMPLATE
        .replace("__GAP__", str(p.gap))
        .replace("__ICON__", str(p.icon))
        .replace("__SUBROW__", str(p.icon + p.gap))
    )


def _pad_style(pad):
    if pad == (12, 12):
        return ""
    fmt = lambda v: f"{v}px" if v else "0"
    return f' style="padding: {fmt(pad[0])} 16px {fmt(pad[1])}"'


def svg(p, height, body_inner, body_class="", pad=(12, 12)):
    cls = ("body " + body_class).strip()
    return (
        f'<svg fill="none" viewBox="0 0 {p.width} {height}" width="{p.width}" height="{height}" '
        f'xmlns="http://www.w3.org/2000/svg">\n'
        f'  <foreignObject width="100%" height="100%">\n'
        f'  <div xmlns="http://www.w3.org/1999/xhtml">\n'
        f'    <style>{style(p)}    </style>\n'
        f'    <div class="{cls}"{_pad_style(pad)}>\n{body_inner}\n    </div>\n'
        f'  </div>\n'
        f'  </foreignObject>\n'
        f'</svg>\n'
    )


def project_row(p, icon, name, desc, sub_text=None, pad=(12, 12), trim=0):
    """A project: icon on the left, name + description (+ optional first sub-line).

    Height is derived from an estimate of how many lines the text wraps to for
    the given profile. `trim` crops empty line-height leading off the bottom of
    the canvas to tighten the gap to whatever follows.
    """
    desc_lines = max(1, math.ceil(len(desc) / p.desc_cpl))
    content = TITLE_H + 2 + desc_lines * LINE_H
    sub_html = ""
    if sub_text:
        sub_lines = max(1, math.ceil(len(sub_text) / p.sub_cpl))
        content += 8 + sub_lines * LINE_H
        sub_html = f'        <ul class="sub"><li>{sub_text}</li></ul>\n'
    height = math.ceil(pad[0] + pad[1] + max(content, p.icon)) - trim
    inner = (
        f'      <img class="icon" src="{icon}" alt=""/>\n'
        f'      <div class="content">\n'
        f'        <span class="name">{name}</span>\n'
        f'        <div class="desc">{desc}</div>\n'
        f'{sub_html}'
        f'      </div>'
    )
    return svg(p, height, inner, "project", pad)


def sub_row(p, text, pad=(12, 12), lift=0):
    """A standalone continuation line, indented to align under a project's text.

    `lift` pulls the line up by N px (negative top margin into the empty line
    leading) and crops the same amount off the bottom, tightening both the gap
    above and the row footprint without clipping any glyphs.
    """
    lines = max(1, math.ceil(len(text) / p.sub_cpl))
    height = math.ceil(pad[0] + pad[1] + lines * LINE_H) - lift
    subrow_style = f' style="margin-top: -{lift}px"' if lift else ""
    inner = (
        f'      <div class="subrow"{subrow_style}>\n'
        f'        <ul class="sub"><li>{text}</li></ul>\n'
        f'      </div>'
    )
    return svg(p, height, inner, pad=pad)


EMULATOR = "Emulator written in C++, using the ncurses library."
LCC = "ANSI C compiler, by implementing a backend for the lcc retargetable compiler."

MAIN_REPO_16 = "Main repository with documentation, schematics and some tools."
MAIN_REPO = "Main repository with documentation, images and some tools."

# A row is one SVG file plus how the README links/labels it. `build` renders the
# SVG for a given Profile; `href` is None for non-clickable rows (the heading);
# `alt` is the image alt text.
Row = namedtuple("Row", "file build href alt")

ROWS = [
    Row(
        "heading.svg",
        lambda p: svg(p, 60, '      <h2>Some of my projects</h2>'),
        None,
        "Some of my projects",
    ),
    Row(
        "desktop-plus.svg",
        lambda p: project_row(
            p, desktopPlus, "Desktop Plus",
            "A GitHub Desktop fork that adds some features I needed for my workflow. It includes commit search, Bitbucket/GitLab support, multiple stashes per branch, and many small features and improvements. Additionally, I keep it up to date with the latest upstream releases, since the shiftkey fork is no longer maintained.",
        ),
        "https://github.com/desktop-plus/desktop-plus",
        "Desktop Plus | A GitHub Desktop fork with commit search, Bitbucket/GitLab support, multiple stashes per branch and more.",
    ),
    Row(
        "doot.svg",
        lambda p: project_row(
            p, terminal, "doot",
            "It turns out that all existing dotfile managers suck, and writing my own is the only way to go. It's designed to be intuitive and <em>extremely</em> fast, while also supporting advanced features such as private (encrypted) files, host-specific alternative files and bootstrapping repositories.",
        ),
        "https://github.com/pol-rivero/doot",
        "doot | An intuitive and extremely fast dotfile manager with encrypted files, host-specific alternatives and bootstrapping.",
    ),
    Row(
        "discord-audio-stream.svg",
        lambda p: project_row(
            p, discord, "Discord Audio Stream",
            "It's very easy to share your screen using Discord. Being able to hear it, not so much. This tool gives you control over the audio that you send to Discord, making it possible to share a screen with audio, use OBS, and any other use case you can think of.",
        ),
        "https://github.com/pol-rivero/DiscordAudioStream",
        "Discord Audio Stream | Control the audio you send to Discord to share a screen with audio, use OBS, and more.",
    ),
    Row(
        "cesc16.svg",
        lambda p: project_row(
            p, chip, "CESC16",
            "A custom CPU, designed from scratch and built on PCBs. Completely 16-bit, with support for interrupts and improved General Purpose IO (GPIO) ports.",
            sub_text=MAIN_REPO_16,
            pad=(12, 0),
            trim=4,
        ),
        "https://github.com/pol-rivero/CESC16",
        "CESC16 | A custom 16-bit CPU designed from scratch and built on PCBs, with interrupts and GPIO ports.",
    ),
    Row(
        "cesc16-emulator.svg",
        lambda p: sub_row(p, EMULATOR, pad=(0, 2), lift=2),
        "https://github.com/pol-rivero/CESC16-emulator",
        "CESC16 emulator written in C++ using the ncurses library.",
    ),
    Row(
        "cesc16-lcc.svg",
        lambda p: sub_row(p, LCC, pad=(2, 12), lift=2),
        "https://github.com/pol-rivero/lcc",
        "CESC16 ANSI C compiler, an lcc backend.",
    ),
    Row(
        "cesca.svg",
        lambda p: project_row(
            p, chip, "CESC",
            "Previous CPU architecture, inspired by Ben Eater's SAP-1 and built on breadboards. It's an 8-bit architecture with a very simple instruction set.",
            sub_text=MAIN_REPO,
        ),
        "https://github.com/pol-rivero/CESCA",
        "CESC | An 8-bit CPU inspired by Ben Eater's SAP-1 and built on breadboards.",
    ),
    Row(
        "arduino-vga.svg",
        lambda p: project_row(
            p, chip, "Arduino VGA Terminal",
            "Use an Arduino Nano to drive a VGA monitor. It only supports text output, so it's great as a terminal for your homebrew CPU projects.",
        ),
        "https://github.com/pol-rivero/ArduinoVGA",
        "Arduino VGA Terminal | Drive a VGA monitor from an Arduino Nano as a text terminal.",
    ),
]


def generate():
    """Write every row SVG (all profiles) and return the README markdown."""
    for profile, _ in VARIANTS:
        os.makedirs(os.path.join(ROWS_DIR, profile.name), exist_ok=True)

    lines = ["<div>"]
    for row in ROWS:
        with open(os.path.join(ROWS_DIR, row.file), "w", encoding="utf-8") as f:
            f.write(row.build(DESKTOP))

        sources = ""
        for profile, media in VARIANTS:
            with open(os.path.join(ROWS_DIR, profile.name, row.file), "w", encoding="utf-8") as f:
                f.write(row.build(profile))
            sources += f'<source media="{media}" srcset="rows/{profile.name}/{row.file}">'

        img = f'<img src="rows/{row.file}" width="100%" alt="{row.alt}">'
        picture = f"<picture>{sources}{img}</picture>"
        lines.append(f'  <a href="{row.href}">{picture}</a>' if row.href else f"  {picture}")
    lines.append("</div>")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    generate()
    profiles = [DESKTOP, MEDIUM, SMALL, MOBILE]
    print(f"{'':24} " + "  ".join(f"{p.name:>16}" for p in profiles))
    for row in ROWS:
        sizes = []
        for p in profiles:
            box = row.build(p).split('viewBox="0 0 ')[1].split('"')[0]
            sizes.append(f"[{box}]")
        print(f"{row.file:24} " + "  ".join(f"{s:>16}" for s in sizes))
