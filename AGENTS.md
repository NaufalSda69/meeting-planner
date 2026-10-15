# AGENTS.md

## Repository state

- Greenfield: no source code, manifests, CI, or git repo yet — only `.venv/`.
- Directory name contains a space (`Workshop Vibecode`); always quote paths in shell commands.

## Python environment

- Use the existing venv; do not install packages globally.
  - Windows PowerShell: `.venv\Scripts\Activate.ps1`
  - Python 3.14.6, pip-managed (no lockfile yet).
- Pre-installed stack (verify with `.venv\Scripts\pip.exe list` before adding deps):
  - App: `streamlit`, `uvicorn`, `starlette`, `websockets`
  - Data: `numpy`, `pandas`, `pyarrow`, `altair`, `pillow`
  - Test/lint-adjacent: `pytest` (only test tool present)
- There is no requirements.txt/pyproject yet. If you add project deps, pin them in a
  `pyproject.toml` or `requirements.txt` and keep the venv in sync.

## Conventions

- Run app: `.venv\Scripts\streamlit run app.py`. UI smoke tests use
  `streamlit.testing.v1.AppTest` (no browser needed); logic tests use pytest.
- No lint/typecheck/format tooling is configured. If you introduce any (e.g. ruff, mypy),
  document the exact commands here in the same commit.
- Tests: `test_logic.py` at repo root; run with `.venv\Scripts\pytest.exe`.
- Pure logic lives in `logic.py` (no Streamlit imports); UI will go in `app.py`;
  feature spec with acceptance tests is `SPEC.md` — keep behavior changes in sync with it.
