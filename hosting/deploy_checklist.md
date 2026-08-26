# Deploy checklist — ReAct Research Agent

This is the project's "definition of done." Walk it top to bottom. Don't tick a box you
haven't actually verified by running the command — "should work" isn't the same as "works."

Commands assume you're inside `build_from_scratch/` unless noted.

## Runs locally

- [ ] Fresh virtual environment, dependencies installed cleanly:
      `python -m venv .venv ; .\.venv\Scripts\Activate.ps1` then `pip install -r requirements.txt`
- [ ] The corpus exists (regenerate if a file is missing): `python generate_data.py` — writes
      the eight `.txt` pages to `data\corpus\`.
- [ ] The CLI answers the demo question with citations:
      `python -m research_agent "What causes coral bleaching and what are its main effects?"`
- [ ] The reasoning trace prints (search → read → read → read → finish):
      `python -m research_agent "What causes coral bleaching and what are its main effects?" --steps`
- [ ] JSON output works: add `--json` to the command above and confirm it parses.
- [ ] Reflection pulls in a second source when starved:
      `python -m research_agent "What causes coral bleaching and what are its main effects?" --max-reads 1`
      — the final answer cites two sources, not one.
- [ ] The Streamlit demo launches and answers in the browser: `streamlit run web_app.py`

## Tests pass

- [ ] `pytest` from `build_from_scratch/` is all green (29 tests).
- [ ] You ran it in the fresh venv, not just your everyday one, so you know the deps are complete.
- [ ] Tests are offline — they ran with NO `GEMINI_API_KEY`, NO `TAVILY_API_KEY`, and NO network.

## README is recruiter-ready

- [ ] `build_from_scratch/README.md` exists and covers: the problem, skills demonstrated,
      tech stack, how it works, how to run it, and what you learned.
- [ ] A real sample-output block is pasted in (not paraphrased) — the `--steps` trace plus the
      final cited answer and its Sources list.
- [ ] A screenshot is embedded (the Streamlit answer with the reasoning-trace expander open).
      A placeholder line is fine until you capture the real one, but capture it before you call
      this done.

## Secrets are clean

- [ ] `.gitignore` contains `.env` (plus `__pycache__/`, `.venv/`, `.pytest_cache/`).
- [ ] `git status` shows `.env` is NOT tracked.
- [ ] `git ls-files | Select-String "\.env$"` prints nothing — only `.env.example` may appear
      if you widen the pattern. If a real `.env` is there, remove it and rotate both keys — see
      the hosting guide's troubleshooting.
- [ ] No API key is hardcoded anywhere in the source.

## The corpus is committed

- [ ] `git ls-files data/corpus` lists all eight `.txt` pages. The deployed app reads these at
      runtime, so they must be in the repo — they are source data, not junk.

## Requirements are present

- [ ] `requirements.txt` lists every runtime dep with a `>=` floor (pydantic, streamlit, and
      the `--real`-only extras: litellm, python-dotenv, tavily-python, trafilatura, httpx). A
      clean `pip install -r requirements.txt` succeeds.
- [ ] `requirements-dev.txt` pulls in the app plus pytest/ruff (it starts with
      `-r requirements.txt`).

## Pushed to GitHub

- [ ] Repo created empty on github.com (no auto README/license), named
      `react-research-agent`, public.
- [ ] `git init` → `git add .` → `git commit` → `git branch -M main` →
      `git remote add origin ...` → `git push -u origin main` all done.
- [ ] Files visible on the GitHub repo page after a refresh; `.env` absent, `data/corpus/`
      present.

## CI is green

- [ ] `.github/workflows/ci.yml` is committed and pushed.
- [ ] The Actions tab shows a completed run with a green checkmark.
- [ ] If it was red, you read the log and fixed the cause (usually a missing dep), then
      re-ran to green.

## Deployed

- [ ] The **Streamlit demo** is live on Streamlit Community Cloud or Hugging Face Spaces, and
      the public URL opens.
- [ ] The **main-file path** is `build_from_scratch/web_app.py` (Streamlit Cloud) — or the
      `build_from_scratch/` contents sit at the Space root (Hugging Face).
- [ ] You asked the demo question on the live site and confirmed: the cited answer renders, the
      three sources render, and the reasoning-trace expander shows five steps.
- [ ] Deploy URL added to the README so a recruiter can click it.

## Repo pinned

- [ ] `react-research-agent` is pinned on your GitHub profile so it shows up first.

When every box is ticked, the project is done and presentable. Send the repo link (and the
live URL) with confidence.
