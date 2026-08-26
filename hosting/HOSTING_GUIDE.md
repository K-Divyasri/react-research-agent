# Publishing the ReAct Research Agent

The star of this project is a **Streamlit web app** (`build_from_scratch/web_app.py`). You
type a research question, and the page shows the cited answer, the numbered sources, the
agent's self-critique, and — in an expander — the full reason → act → observe trace. Watching
that loop is the whole lesson, so the demo is what you host.

There's no separate API and no Docker here (project 5 had those; this one doesn't need them).
You put the code on GitHub with tests running automatically, then deploy the Streamlit app to
a free host and send someone the link.

The big thing to know up front: **it runs offline by default.** The agent reasons over a
bundled eight-page corpus with a keyword search — no language model, no network, no API key.
So a public deploy is genuinely free, forever, even while it's live. You only touch secrets
if *you* choose to turn on the `--real` path (a live model + real web search), and that's
optional and at the very end.

A note on layout before you start: this repo publishes the **whole project folder**
(`12-react-research-agent/`), with `build_from_scratch/` as a subfolder. That way your GitHub
page shows the learning material *and* the polished package. The Git commands below run from
the **project root**; the app itself lives one level down in `build_from_scratch/`, which is
why the deploy steps point at `build_from_scratch/web_app.py`.

---

## Step 0 — Install Git and make a GitHub account

Git tracks versions of your files on your laptop. GitHub is the website that stores a copy
online. Different things: Git is local, GitHub lives on the internet. You need both.

### Install Git

1. Go to https://git-scm.com/download/win. The download starts on its own.
2. Run the installer. Click Next through every screen — the defaults are fine.
3. Open a **new** PowerShell window (new, so it picks up the install) and check:

```powershell
git --version
```

If you see something like `git version 2.45.0`, you're set. If PowerShell doesn't recognize
`git`, close every terminal, open a fresh one, and try again.

### Make a GitHub account

1. Go to https://github.com and sign up (use `mathuransada@gmail.com`, the one on file).
   Verify the email.
2. Pick a username you'd put on a CV — recruiters see it. `divya-dev` beats `xX_coder_Xx`.

### Tell Git who you are (once per machine)

```powershell
git config --global user.name "Your Name"
git config --global user.email "mathuransada@gmail.com"
```

---

## Step 1 — Know what must NOT go in the repo

One file must never leave your laptop, and the shipped `.gitignore` already blocks it:

- **`.env`** — if you ever use `--real`, this holds your `GEMINI_API_KEY` and
  `TAVILY_API_KEY`. A key is a password. Commit it and it's on the public internet
  **forever** (Git keeps history; bots scrape GitHub within minutes and can run up a bill on
  your account). The repo ships `.env.example` instead — variable names with blank values,
  safe to commit.

Open `build_from_scratch/.gitignore` and confirm it lists at least `.env`, `__pycache__/`,
`.venv/`, and `.pytest_cache/`. It does — but check, because this is the part that bites
people. The rule: **source, config, docs, and the corpus go in; secrets and machine junk
stay out.**

One thing that *does* belong in the repo and surprises people: the corpus text files under
`build_from_scratch/data/corpus/`. Those eight `.txt` files are the agent's entire "internet"
when it runs offline. They're source data, not junk — the deployed app reads them at runtime,
so they must be committed. `git add .` picks them up; just don't add them to `.gitignore`.

---

## Step 2 — Make the local repo and commit

From the **project root** (`12-react-research-agent/`, the folder with `build_from_scratch/`
and `generate_data.py` in it):

```powershell
git init
git add .
git commit -m "Initial commit: ReAct Research Agent (reason-act-observe loop, cited answers, offline)"
```

`git init` creates the hidden `.git` folder. `git add .` stages everything except what
`.gitignore` excludes. `git commit` saves the snapshot.

Now the single most important check in this guide:

```powershell
git status
git ls-files | Select-String "\.env$"
```

The second command should print **nothing** (or only `.env.example` if you widen the
pattern), and **never** a bare `.env`. It should list the corpus files under
`build_from_scratch/data/corpus/`. If a real `.env` shows up as tracked, you committed
something you shouldn't — fix it with the troubleshooting section at the bottom before you
push.

---

## Step 3 — Create the empty repo on GitHub and push

1. On github.com (signed in), top-right **+** then **New repository**.
2. Name it `react-research-agent` (lowercase, hyphens).
3. Description: *"A ReAct agent that answers a research question with cited sources. Reasons,
   searches, and reads over a small corpus. Runs offline, no API key."*
4. Leave it **Public**.
5. Do **not** tick "Add a README", ".gitignore", or "license" — the repo must be empty or
   your first push collides.
6. **Create repository.**

Then, back in PowerShell at the project root:

```powershell
git branch -M main
git remote add origin https://github.com/YOURNAME/react-research-agent.git
git push -u origin main
```

The first push opens a browser sign-in to authenticate. Do it. GitHub turned off terminal
passwords years ago — use the browser sign-in (easiest) or a Personal Access Token as the
password (troubleshooting below). Refresh the repo page; your code is live.

---

## Step 4 — Add CI so the tests run on every push

CI (Continuous Integration) proves your tests pass on a clean machine, not just your laptop,
every time you push. Green checkmark = recruiters notice, and it catches the classic "works
on my machine" bug. This project's suite is **offline and keyless**, so CI never needs a
secret and never costs anything.

There's a ready workflow in this folder at `hosting/github_actions/ci.yml`. It only runs if
it lives at `.github/workflows/` in the repo. From the project root:

```powershell
mkdir .github\workflows
copy hosting\github_actions\ci.yml .github\workflows\ci.yml
git add .github\workflows\ci.yml
git commit -m "Add GitHub Actions CI (offline pytest on every push)"
git push
```

Open the repo's **Actions** tab and watch it run: checkout, install Python 3.12, install
`build_from_scratch/requirements-dev.txt`, run `pytest` from `build_from_scratch/`. Green
means all 29 tests passed on GitHub's machine. If it's red, click the failed step and read
the log bottom-up — the real error is in the last few lines.

Once green, grab a status badge (Actions page → `...` → **Create status badge**) and paste
the markdown at the top of `build_from_scratch/README.md`.

---

## Deploy the demo — pick one free host

Both hosts below run the app straight from your GitHub repo. Both are free. Pick one (do both
if you want two links). Either way the app defaults to offline mode, so **no secret is
needed** to get a working public demo.

### Option A — Streamlit Community Cloud (easiest public URL)

1. Go to https://share.streamlit.io and sign in with GitHub.
2. **New app** → **Deploy a public app from GitHub** → pick your `react-research-agent` repo
   and the `main` branch.
3. **Main file path:** `build_from_scratch/web_app.py`. This is the part people get wrong —
   the app file is *inside* `build_from_scratch/`, not at the repo root, so the path has to
   include that folder. Getting it right is what lets `from research_agent.agent import
   research` resolve, because Streamlit puts the app file's own folder on the import path.
4. Advanced settings → set the Python version to 3.12 if offered. Streamlit reads
   dependencies from `build_from_scratch/requirements.txt` automatically — it lives right next
   to the app file, so you don't configure it.
5. **Deploy.** First build takes a couple of minutes. You get a
   `https://YOURNAME-....streamlit.app` URL.

If the build fails with a `ModuleNotFoundError: research_agent`, it's almost always the
main-file path — it must be `build_from_scratch/web_app.py`, not `web_app.py`.

### Option B — Hugging Face Spaces (Streamlit SDK)

1. Go to https://huggingface.co/spaces → **Create new Space**.
2. Name it, choose **Streamlit** as the SDK, keep it **Public**, pick the free CPU tier.
3. Spaces expects the app entry file at the **Space root**, and it doesn't understand a
   `build_from_scratch/` subfolder the way Streamlit Cloud does. So in the Space's **Files**
   tab, upload the *contents* of `build_from_scratch/` at the top level:
   - `web_app.py`
   - the `research_agent/` folder (the whole package)
   - `requirements.txt`
   - the `data/` folder (this carries `data/corpus/` — the app can't answer anything without
     it)
4. In the Space **Settings**, set the **app file** to `web_app.py` (it's at the root now).
5. Spaces serves Streamlit on **port 7860** internally and wires that up for you — the SDK
   handles the port, so you don't set it anywhere. Spaces then installs `requirements.txt`
   and launches the app automatically. Watch the build log on the Space page; when it turns
   green you have a public URL.

The most common Spaces failure is a blank corpus: if you forgot to upload the `data/` folder,
the app loads but every question returns nothing. Re-upload `data/corpus/` and rebuild.

---

## Secrets — only if you turn on `--real`

Everything above is offline and needs **no secret**. You only need keys if you deliberately
switch the app to the live path — a real language model plus real web search instead of the
bundled corpus. The shipped `web_app.py` runs offline; you'd only wire in `--real` if you
extend it yourself. When you do, two keys are involved, and they go in each host's Secrets UI
— **never** in the repo:

- **`GEMINI_API_KEY`** — the language model, via LiteLLM. Free from
  https://aistudio.google.com/apikey.
- **`TAVILY_API_KEY`** — real web search. Free tier from https://tavily.com.

Where to put them:

- **Streamlit Community Cloud:** App → **Settings** → **Secrets**, add
  `GEMINI_API_KEY = "..."` and `TAVILY_API_KEY = "..."` (TOML format, one per line).
- **Hugging Face Spaces:** Space → **Settings** → **Variables and secrets** → **New secret**,
  add each key by name.

The code reads these from the environment (via `python-dotenv` locally), so you never write a
key into any committed file. Optionally set `AGENT_MODEL` the same way to switch models (it
defaults to `gemini/gemini-1.5-flash`). Leave all of this alone and the free offline demo
works fine — that's the whole point of offline-first.

---

## Verify the deploy

Once the app is live, prove it works from a browser — no terminal needed, which is exactly
why a demo like this is worth having.

1. Open your `.streamlit.app` (or Space) URL.
2. In the question box, ask the demo question:
   **What causes coral bleaching and what are its main effects?**
3. Click **Research** and confirm three things render:
   - **The answer** — three sentences, each ending in a numbered citation like `[1]`, `[2]`,
     `[3]`. It should read: *"The main effects of coral bleaching are a loss of biodiversity,
     a decline in fisheries, and weaker coastal protection. [1] ..."*
   - **The Sources list** — three entries, `[1]` Effects of Coral Bleaching on Reef
     Ecosystems, `[2]` What Is Coral Bleaching?, `[3]` Causes of Coral Bleaching. Every `[n]`
     in the answer maps to one of these.
   - **The reasoning trace** — expand *"Show the full reasoning trace (reason → act →
     observe)"* and you should see five steps: search, read, read, read, finish.
4. Bonus check: in the sidebar, drag **Sources to read** down to **1** and ask again. The
   answer now cites just two sources, and the self-critique note tells you the reflection step
   pulled in the second one. That's the stretch-goal reflection working in the live app —
   a nice thing to screenshot.

Take a screenshot of the answer with its trace expanded and drop it in
`build_from_scratch/README.md`. That image is what makes a recruiter click the link.

---

## Troubleshooting (Git)

**You committed `.env` by accident.** Treat the keys as compromised — go to Google AI Studio
and Tavily and **rotate them** immediately (if you pushed, they're already public). Then
untrack the file (keeps it on disk):

```powershell
git rm --cached .env
git commit -m "Remove committed .env"
git push
```

`git rm --cached` only stops tracking it going forward — the old value still sits in Git
history, which is exactly why you rotate the keys rather than trusting the delete.

**`error: failed to push` / push rejected.** The remote has commits yours doesn't — usually
because you let GitHub add a README/license. Replay your work on top:

```powershell
git pull origin main --rebase
git push
```

**Authentication fails on push.** GitHub won't accept your account password in the terminal.
Easiest fix: install the GitHub CLI from https://cli.github.com, run `gh auth login`, follow
the browser prompts. Or generate a Personal Access Token (Settings → Developer settings →
Tokens (classic), `repo` scope) and paste it as the password when prompted.

**`git: command not found` right after installing.** You're in a terminal opened before the
install. Close every PowerShell window and open a fresh one.
