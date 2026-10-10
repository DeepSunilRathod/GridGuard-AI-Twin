# GridGuard AI Twin - UI Upgrade

This frontend upgrade integrates all four UI areas in one React/Vite application:
A. Operational overview (existing)
B. Interactive digital substation single-line diagram (added)
C. Four sensor trend charts (added)
D. AI evaluation, fault demo, AI prediction and chatbot (existing components restyled)

## Install/run on Windows

1. Make a backup of your existing `D:\GridGuard-AI-Twin\frontend\src` folder.
2. Extract this ZIP.
3. Copy the extracted `src` folder into `D:\GridGuard-AI-Twin\frontend\src`, replacing files when prompted.
   - Or copy only `App.jsx` and `App.css` if you want to preserve your current evaluation/chatbot/fault panel files. The CSS upgrade references their existing class names.
4. From Command Prompt:
   ```
   cd /d D:\GridGuard-AI-Twin\frontend
   npm install
   npm run dev
   ```
5. Keep FastAPI running at `http://127.0.0.1:8000`.
6. Keep the Streamlit simulator running at `http://localhost:8501`.

## Notes
- The UI keeps the existing API base URL (`http://127.0.0.1:8000`) and existing API calls.
- The single-line diagram reads current `assets` data from the dashboard state and selecting a feeder updates the shared React selected-asset state.
- The new sensor analytics charts use the existing selected asset's `chartData` history and field names.
- The twin and sensor values are software-simulated, not physical measurements.
- RUL and AI prediction limitations remain as described by the existing backend.
- JSX syntax was checked. A production build could not be completed in this environment because the uploaded `node_modules` contains Windows-specific native packages; install dependencies on Windows with `npm install` before running/building.


## UI fixes included
- Extended the 11 kV busbar leftwards so the TX-01, TX-02, and TX-03 feeder drops all connect to it.
- Fixed low-contrast AI evaluation metric/table colors for the dark theme.
- Fixed the assistant and user message bubbles, chatbot suggestions, and input field to use readable dark-theme colors.
