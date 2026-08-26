"""A one-page Streamlit UI for the research agent -- the free live demo.

The point of this page is to make the agent's *thinking* visible. You type a
question, and it shows the cited answer, the numbered sources, the self-critique,
and -- expandable -- the full reason/act/observe trace. Watching the loop is the
whole lesson, so the trace gets pride of place.

Run it locally:

    streamlit run web_app.py

Deploy it free on Hugging Face Spaces or Streamlit Community Cloud (see
../hosting/HOSTING_GUIDE.md). It runs OFFLINE by default over the bundled corpus,
so it needs no key and costs nothing even when hosted.
"""

from __future__ import annotations

import streamlit as st

from research_agent.agent import research
from research_agent.corpus import load_pages

EXAMPLES = [
    "What causes coral bleaching and what are its main effects?",
    "How have mass bleaching events affected the Great Barrier Reef?",
    "What can be done to reduce coral bleaching?",
]


def main() -> None:
    st.set_page_config(page_title="ReAct Research Agent", page_icon="🔎")
    st.title("🔎 ReAct Research Agent")
    st.caption("Ask a question. The agent searches, reads, and answers with citations. "
               "Runs offline over a small built-in corpus -- no API key needed.")

    with st.sidebar:
        st.header("Settings")
        max_reads = st.slider("Sources to read", 1, 5, 3,
                              help="Set this to 1 to watch the reflection step pull in a second source.")
        reflect = st.checkbox("Reflection pass", value=True)
        st.markdown("**The corpus** (its whole 'internet'):")
        for p in load_pages():
            st.markdown(f"- {p.title}")

    question = st.text_input("Your question", value=EXAMPLES[0])
    st.caption("Try: " + " · ".join(f"_{e}_" for e in EXAMPLES[1:]))

    if st.button("Research", type="primary"):
        if not question.strip():
            st.error("Type a question first.")
            return
        with st.spinner("Reasoning, searching, reading..."):
            report = research(question, max_reads=max_reads, reflect=reflect)

        st.subheader("Answer")
        st.write(report.answer)

        st.subheader("Sources")
        for s in report.sources:
            st.markdown(f"**[{s.n}] {s.title}** — `{s.locator}`  \n> {s.snippet}")

        if report.reflection:
            st.subheader("The agent's self-critique")
            st.info(report.reflection)

        with st.expander("Show the full reasoning trace (reason → act → observe)"):
            for step in report.steps:
                act = step.action + (f" · {step.action_input}" if step.action_input else "")
                st.markdown(f"**{step.n}. {act}**  \n"
                            f"*thought:* {step.thought}  \n"
                            f"*observation:* {step.observation}")


if __name__ == "__main__":
    main()
