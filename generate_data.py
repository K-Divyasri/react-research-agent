"""Write the offline 'mini-web' this research agent practises on.

Run this once, first:

    python generate_data.py

A real research agent calls a live search API and downloads real web pages. That
is impossible to run in a test, a notebook, or on a train with no wifi -- and it
costs money. So this project ships its own tiny, fixed corpus of eight documents
under `data/corpus/`. The offline search tool indexes THESE files and the offline
"read page" tool returns their text. Nothing leaves your machine.

The corpus is built around one research question -- coral bleaching -- with five
genuinely relevant pages and three distractors (precious-coral jewellery, reef
tourism economics, and a totally unrelated page about caffeine). The distractors
matter: they are what make search *ranking* a real problem. A dumb agent that
reads everything wastes steps; a good one reads the pages that actually answer the
question. The facts in these pages are real and roughly accurate, kept short on
purpose.

There is no randomness here. Same files, byte for byte, every run -- so every
notebook, lab and test can assert exact behaviour.
"""

from __future__ import annotations

from pathlib import Path

# Each entry: filename -> (title, body). The first line the agent "sees" as the
# page title; the body is what it reads. Sentences are kept short so the agent's
# extractive summary picks up clean, quotable facts.
DOCS: dict[str, tuple[str, str]] = {
    "01_what_is_coral_bleaching.txt": (
        "What Is Coral Bleaching?",
        """\
Coral bleaching is what happens when a coral turns white and loses its colour.
Corals are animals that live in partnership with tiny algae called zooxanthellae
which live inside their tissue. These algae photosynthesise and give the coral
both its colour and most of its food. When a coral is stressed, it expels the
algae, and without them the coral turns bone white and begins to starve.
A bleached coral is not dead yet, but it is weakened and at high risk of dying if
the stress continues. If conditions return to normal quickly, the algae can come
back and the coral can recover.
""",
    ),
    "02_causes_of_bleaching.txt": (
        "Causes of Coral Bleaching",
        """\
The primary cause of coral bleaching is rising sea surface temperatures driven by
climate change. Corals are sensitive to heat, and water only one to two degrees
Celsius above the usual summer maximum, sustained for a few weeks, is enough to
trigger mass bleaching. These spikes are often called marine heatwaves.
Other stressors can cause or worsen bleaching too: unusually strong sunlight,
ocean acidification, pollution and farm runoff, freshwater from heavy storms, and
disease. But warming water is by far the main driver of the large-scale events
seen around the world.
""",
    ),
    "03_effects_on_reefs.txt": (
        "Effects of Coral Bleaching on Reef Ecosystems",
        """\
The main effects of coral bleaching are a loss of biodiversity, a decline in
fisheries, and weaker coastal protection. Coral reefs cover less than one percent
of the ocean floor but support around a quarter of all marine species, so when
the coral dies the animals that depend on it disappear too.
Reefs also act as natural breakwaters that absorb wave energy and shield coastlines
from storms and erosion. Hundreds of millions of people rely on reefs for food and
for income from fishing and tourism, so a bleached, dying reef is an economic blow
as well as an ecological one.
""",
    ),
    "04_major_bleaching_events.txt": (
        "Major Mass Bleaching Events",
        """\
Scientists have recorded several global mass bleaching events, each tied to unusually
warm years. The first recognised global event was in 1998, followed by 2010, a long
event from 2014 to 2017, and another beginning in 2023.
Australia's Great Barrier Reef, the largest reef system on Earth, suffered severe
bleaching in 2016, 2017, 2020, and 2022. The 2016 event alone killed a large share
of the corals in the reef's northern section. The shrinking gap between events is a
warning sign, because reefs need roughly a decade to recover and they are no longer
getting it.
""",
    ),
    "05_solutions_and_recovery.txt": (
        "Reducing and Recovering From Bleaching",
        """\
The single most important way to reduce coral bleaching is to cut the greenhouse gas
emissions that warm the ocean, because warming is the root cause. Everything else
buys time rather than fixing the problem.
Local action helps corals cope: marine protected areas, cleaner water with less
pollution and runoff, and limits on overfishing all leave reefs healthier and more
able to bounce back. Scientists are also restoring reefs by growing coral in nurseries
and replanting it, and breeding or selecting heat-tolerant corals that can survive
warmer water.
""",
    ),
    # ---- Distractors below. They share words with the real pages but do NOT answer
    #      a question about the causes and effects of bleaching. ----
    "06_precious_coral_jewellery.txt": (
        "Precious Coral in Jewellery",
        """\
Precious coral, sometimes called red or pink coral, is a hard coral prized for
jewellery and carving for thousands of years. The species most often used belongs
to the genus Corallium and grows slowly in deep Mediterranean and Pacific waters.
Its rich colour comes from the skeleton itself, not from algae, and harvesting it is
now tightly regulated because centuries of collection have depleted the beds. This
kind of coral has nothing to do with the reef-building corals that bleach in warm
water.
""",
    ),
    "07_reef_tourism_economics.txt": (
        "Reef Tourism Economics",
        """\
Coral reefs are a major draw for tourists, who come to dive, snorkel, and visit
coastal towns built around the reef trade. The Great Barrier Reef alone is estimated
to contribute billions of dollars a year to Australia's economy and to support tens
of thousands of jobs.
Tourism operators depend on healthy, colourful reefs, so the industry has become a
loud voice for reef protection. This page is about the money reefs bring in, not
about the biology of why corals lose their colour.
""",
    ),
    "08_caffeine_and_sleep.txt": (
        "Caffeine and Sleep",
        """\
Caffeine is a stimulant found in coffee, tea, and many soft drinks. It works by
blocking adenosine, a chemical in the brain that builds up during the day and makes
you feel sleepy. Because caffeine can stay in the body for many hours, drinking it
late in the afternoon can make it harder to fall asleep at night. This page has
nothing to do with oceans, reefs, or coral.
""",
    ),
}


def main() -> None:
    out_dir = Path(__file__).parent / "data" / "corpus"
    out_dir.mkdir(parents=True, exist_ok=True)
    for filename, (title, body) in DOCS.items():
        # Store the title as the first line, then a blank line, then the body.
        (out_dir / filename).write_text(f"{title}\n\n{body}", encoding="utf-8")
    print(f"Wrote {len(DOCS)} corpus pages to {out_dir}")
    for name in DOCS:
        print(f"  - {name}")


if __name__ == "__main__":
    main()
