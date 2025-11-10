<!-- Project-specific instructions for AI coding agents -->
# Neuro-Dash — Copilot instructions

Purpose: give an AI coding assistant the minimal, actionable context to be productive in this repo.

1) Big-picture architecture
- UI: `app.py` is a Streamlit app (main UI). It instantiates `EEGStreamer` / `BetaWaveProcessor` and `CarRaceGame` via `st.session_state`.
- Backend data source: `eeg_backend.py` contains `EEGStreamer` (hardware vs demo) and `BetaWaveProcessor` (beta-band filtering and focus normalization).
- Headless server: `focus_server.py` provides a CLI UDP publisher that sends normalized focus scores (0.0–1.0) to the game at UDP port 5005.
- Display utilities: `server+display/focus_server.py` (relay for OpenBCI GUI → compute focus → sends to port 5005) and `server+display/focus_display.py` (pygame mock display).
- Game logic: `game_logic.py` contains `CarRaceGame` and `GameState` and is the single source of truth for movement rules and thresholds.
- Persistence: `leaderboard.py` reads/writes `leaderboard.json` in the repo directory.

2) Key integration points & constants (search-edit-safe)
- UDP output port used by focus servers: 5005 (see `focus_server.py`, `server+display/focus_server.py`).
- `server+display/focus_server.py` listens on UDP port 12345 for raw OpenBCI data by default.
- BrainFlow is optional. `eeg_backend.py` sets `BRAINFLOW_AVAILABLE = False` if brainflow import fails. Install `brainflow` only for hardware support (commented in `requirements.txt`).
- Normalization: `BetaWaveProcessor.get_focus_score` maps raw beta power → 0.0–1.0 using these project-specific rules: max_power = threshold * 3.5, score = (raw/max_power)**0.5 with an extra penalty above 0.75. If you change normalization, update usages and UI copy.
- Game thresholds: `CarRaceGame` defaults to a normalized `focus_threshold` of 0.80 and `min_focus_to_move` ≈ 0.75. These are intentionally strict; changing them requires consistent updates in `app.py` UI slider help text and `game_logic.py`.

3) How to run (examples observed in repo)
- Run UI (recommended):
  - streamlit run app.py
  - or: python app.py (app.py contains a __main__ but Streamlit is expected for best UX)
- Run focus server (demo):
  - python focus_server.py --demo
- Run focus server (hardware, example):
  - python focus_server.py --board-type Ganglion --serial-port COM3
- Mock display: python server+display/focus_display.py

4) Project-specific conventions & patterns to preserve
- Streamlit state: `st.session_state` stores long-lived objects (eeg_streamer, eeg_processor, game, leaderboard). Always check for keys before replacing to avoid leaking hardware sessions.
- Demo vs hardware branching: `EEGStreamer(use_demo=True)` vs `EEGStreamer(use_demo=False)` and the `BRAINFLOW_AVAILABLE` flag gate hardware paths — keep that pattern for graceful degradation.
- Two different focus semantics:
  - UI slider `focus_threshold` in `app.py` is a beta-power threshold (10–100); it's passed into `BetaWaveProcessor.get_focus_score(beta_power, threshold)` which returns normalized 0–1.
  - Game `focus_threshold` in `CarRaceGame` is normalized (0.0–1.0). Don't mix these without an explicit conversion.
- Visual/feedback loops: The code uses blocking sleep + rerun for Streamlit refresh (e.g., `time.sleep(...)` + `st.rerun()` in `app.py`). Keep changes minimal here — altering refresh rates affects sampling and display.

5) Safe edit tips & examples
- If adjusting difficulty or normalization, update both `eeg_backend.get_focus_score` and `game_logic` constants. Example locations:
  - eeg_backend.py -> BetaWaveProcessor.get_focus_score (max_power = threshold * 3.5, **power 0.5 scaling**, extra penalty >0.75)
  - game_logic.py -> CarRaceGame.focus_threshold (0.80), min_focus_to_move (0.75), and speed scaling in update().
- When adding hardware support or testing BrainFlow paths locally, guard tests/CI to skip brainflow imports when not installed (the repo currently prints a warning and falls back to demo mode).
- For networking changes, preserve the current ports (5005, 12345) unless you update all callers.

6) Files to inspect when debugging a change
- UI & wiring: `app.py`
- Data acquisition & processing: `eeg_backend.py`
- CLI server for headless mode: `focus_server.py`
- Game mechanics: `game_logic.py`
- Persistence: `leaderboard.py` and `leaderboard.json` (created at runtime)
- Display & integration tooling: `server+display/*`

7) Notes / gotchas discovered
- README mentions `focus.py` but the repo's UI lives in `app.py` (use Streamlit). Prefer `streamlit run app.py` for development.
- `requirements.txt` lists core libs; `brainflow` is optional and commented out.
- There are two `focus_server.py` files: a root `focus_server.py` (CLI server) and `server+display/focus_server.py` (relay for OpenBCI GUI). Inspect which one you intend to run.

If any section looks unclear or you'd like me to expand examples (unit tests, code-change checklists, or more command snippets), tell me which area to expand and I will iterate.
