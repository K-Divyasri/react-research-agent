# ReAct Research Agent

A research agent that answers a question with cited sources. It reasons about what it needs,
searches, reads the promising pages, and writes a short answer where every claim points back to
a source it actually read, then critiques its own work. Runs offline with no API key by
default; an optional flag swaps in a real language model and real web search.

**Problem:** Ask a plain chatbot a research question and you get fluent prose with no way to
check it: you can't tell which sentence came from where, or whether any of it is grounded at
all. That's fine for brainstorming and dangerous for anything real. What you actually want is
an agent that behaves like a researcher: figure out what to look up, go read it, and answer
*with receipts*, every claim tied to a specific source, and nothing asserted that wasn't read.
This project builds that agent, and builds the loop that drives it by hand so none of it is
magic.

**Skills demonstrated:** agent design, the ReAct loop (reason → act → observe) implemented from
scratch, tool use behind a clean interface (search + read), keyword search ranking with
distractor documents, grounding and citation discipline (every `[n]` maps to a real source, no
dangling references), a reflection / self-critique pass that repairs a thin answer, a
backend-agnostic tool layer (offline corpus vs. live LiteLLM + Tavily), pydantic v2 schemas,
argparse CLI design, a Streamlit UI, and pytest (29 tests, all offline).

**Tech stack:** Python 3.10+, pydantic 2 for the typed `Report` / `Step` / `Source` models,
Streamlit for the demo UI. The optional `--real` path uses LiteLLM (with a free Gemini key) for
the model and Tavily (free tier) plus trafilatura for real web search and page extraction.
Offline mode, the default everywhere, needs none of those.

## How it works

The package is split so each file does one job, which is also what makes it testable:

```
research_agent/
├── schema.py     the pydantic models: Step, Source, and the final Report -- the CONTRACT
├── corpus.py     the offline "mini-web": load 8 pages, keyword-search and rank them
├── tools.py      the two tools (search, read) behind one backend-agnostic interface
├── planner.py    the "brain": decides the next action; OfflinePlanner and RealPlanner
├── react.py      run_loop() -- owns the transcript, drives reason -> act -> observe
├── agent.py      research(question) -> Report -- the one function most people call
├── cli.py        the argparse front door: python -m research_agent "..."
└── __main__.py   makes `python -m research_agent` work
```

The flow is one loop, then a finish:

```
question
   │
   ▼
┌─────────────────────────────────────────┐
│  reason → act (search | read) → observe  │  ← the ReAct loop, capped by max_steps
└─────────────────────────────────────────┘
   │  (planner decides: keep reading, or finish)
   ▼
compose a cited answer  →  reflect (self-critique)
   │                              │
   │        if the answer is too thin, read ONE more source and recompose
   ▼
Report { answer, sources[], steps[], reflection }
```

The design choice that matters: **the loop and the planner are separate.** `react.py` owns the
transcript and the tool calls but makes no decisions; `planner.py` makes decisions but touches
no tools. That seam is why the *same* loop runs unchanged whether the brain is a deterministic
`OfflinePlanner` or a `RealPlanner` calling a live model: you swap the planner, not the engine.
It's also why the tests can drive the loop with a predictable offline brain and assert exact
behaviour.

The second choice that matters: **grounding is enforced, not hoped for.** The agent only writes
sentences it can attach to a page it read, and every `[n]` in the answer maps to an entry in the
`Source` list. The corpus deliberately includes distractor pages (coral *jewellery*, reef
*tourism*, and an unrelated page on caffeine) so that search *ranking* has to work: a good
agent reads the on-topic pages and skips the noise. Then the reflection pass acts as a cheap
quality gate: if the draft leans on too few sources, the agent reads one more and rewrites,
rather than shipping a thin answer.

The offline planner is deterministic: search first, read the top-ranked unread pages up to
`max_reads`, then finish, so no key and no network are needed to run, test, or host it. The
`--real` path keeps the identical loop but lets a language model choose each action and pulls
pages from the live web, which is the argument for why the abstraction was worth building.

## Run locally

```powershell
python -m venv .venv ; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python generate_data.py                      # writes the 8 corpus pages to data\corpus\

python -m research_agent "What causes coral bleaching and what are its main effects?" --steps
python -m research_agent "What causes coral bleaching and what are its main effects?" --json
python -m research_agent "What causes coral bleaching and what are its main effects?" --max-reads 1
pytest                                        # 29 tests, all offline

streamlit run web_app.py                      # the demo UI
```

The CLI takes a question in quotes, with `--steps` (print the full reason/act/observe trace),
`--json` (the `Report` as JSON), `--max-reads N` (how many sources to read before finishing),
`--max-steps N` (a hard cap on loop turns), `--no-reflect` (skip the self-critique), and
`--real` (use a live model + web search).

### Sample run: the reasoning trace and the cited answer

`python -m research_agent "What causes coral bleaching and what are its main effects?" --steps`:

```
Reasoning trace
------------------------------------------------------------
1. thought: I don't know the answer yet, so I'll search for the question.
   action:  search What causes coral bleaching and what are its main effects?
   observe: 5 results: 03_effects_on_reefs.txt (Effects of Coral Bleaching on Reef Ecosystems); 01_what_is_coral_bleaching.txt (What Is Coral Bleaching?); 02_causes_of_bleaching.txt (Causes of Coral Bleaching); 06_precious_coral_jewellery.txt (Precious Coral in Jewellery); 05_solutions_and_recovery.txt (Reducing and Recovering From Bleaching)
2. thought: 'Effects of Coral Bleaching on Reef Ecosystems' looks relevant. I'll read it to get the details.
   action:  read 03_effects_on_reefs.txt
   observe: Read 'Effects of Coral Bleaching on Reef Ecosystems' (577 characters).
3. thought: 'What Is Coral Bleaching?' looks relevant. I'll read it to get the details.
   action:  read 01_what_is_coral_bleaching.txt
   observe: Read 'What Is Coral Bleaching?' (584 characters).
4. thought: 'Causes of Coral Bleaching' looks relevant. I'll read it to get the details.
   action:  read 02_causes_of_bleaching.txt
   observe: Read 'Causes of Coral Bleaching' (575 characters).
5. thought: I've read the most relevant pages. I have enough to write the answer.
   action:  finish
   observe: Ready to write the answer.
------------------------------------------------------------

The main effects of coral bleaching are a loss of biodiversity, a decline in fisheries, and weaker coastal protection. [1] Coral bleaching is what happens when a coral turns white and loses its colour. [2] The primary cause of coral bleaching is rising sea surface temperatures driven by climate change. [3]

Sources:
  [1] Effects of Coral Bleaching on Reef Ecosystems (03_effects_on_reefs.txt)
  [2] What Is Coral Bleaching? (01_what_is_coral_bleaching.txt)
  [3] Causes of Coral Bleaching (02_causes_of_bleaching.txt)

Reflection: The answer draws on 3 sources and every claim carries a citation. It holds up.
```

Notice the agent read the three on-topic pages and skipped `06_precious_coral_jewellery.txt`
even though search surfaced it, the ranking earned its keep, and every citation in the answer
maps to a source it actually opened.

### Sample run: reflection repairs a thin answer

Starve it with `--max-reads 1` and the self-critique step does real work:

`python -m research_agent "What causes coral bleaching and what are its main effects?" --max-reads 1`:

```
The main effects of coral bleaching are a loss of biodiversity, a decline in fisheries, and weaker coastal protection. [1] Coral bleaching is what happens when a coral turns white and loses its colour. [2]

Sources:
  [1] Effects of Coral Bleaching on Reef Ecosystems (03_effects_on_reefs.txt)
  [2] What Is Coral Bleaching? (01_what_is_coral_bleaching.txt)

Reflection: The answer draws on 2 sources and every claim carries a citation. It holds up.
```

The agent read one page, drafted an answer with a single source, and its reflection flagged that
as too thin, so it read one more page (`01_what_is_coral_bleaching.txt`, on a step whose thought
says *"My reflection flagged too few sources, so I'll read one more."*) and rewrote the answer to
cite two. That's the stretch-goal self-critique loop closing on its own.

### The Streamlit demo

`streamlit run web_app.py` opens a one-page site: type a question, and it shows the cited answer,
the numbered sources, the self-critique, and, in an expander, the full reason → act → observe
trace. The sidebar lets you drop **Sources to read** to 1 to watch reflection add a source live.
It runs offline, so it's free to host with no key. See `hosting/HOSTING_GUIDE.md`.

### The optional `--real` path

Copy `.env.example` to `.env`, add a free Gemini key (https://aistudio.google.com/apikey) and a
free Tavily key (https://tavily.com), then:

```powershell
python -m research_agent "Your own question here" --real
```

The identical loop now runs against a live model and the real web instead of the bundled corpus.
Without keys, offline mode is the default and everything else works untouched.

## What I learned

- **An agent is a loop over tools, nothing more mystical than that.** Once I'd written
  `run_loop` by hand, the ReAct pattern stopped being a buzzword: reason a step, call a tool,
  read the result, decide again. Building it myself is why I can explain exactly where a real
  framework would slot in.
- **Separating the planner from the loop is what makes the whole thing swappable.** The loop
  owns the transcript and the tools; the planner only decides. That one seam is why the same
  engine runs a deterministic offline brain *and* a live model with zero changes to the loop,
  and why the tests can drive it predictably.
- **Grounding has to be enforced, not trusted.** Making every `[n]` resolve to a real source,
  and only writing claims I could attach to a page the agent read, is the difference between a
  citation and decoration. A dangling reference is a bug.
- **Reflection is a cheap, real quality gate.** A single self-critique pass that asks "is this
  answer thin?" and reads one more source when the answer is caught the exact failure mode,
  a confident answer built on too little, that makes agents untrustworthy.
- **Distractors are how you prove search ranking works.** Padding the corpus with tempting
  near-misses (coral jewellery, reef tourism) meant "the agent read the right pages" became
  something I could actually test, not just hope for.
