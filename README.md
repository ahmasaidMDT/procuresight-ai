## Run ProcureSight AI locally

You’ll need Git, uv, and Node.js with npm. The Python backend uses
Python 3.12. The saved models are included in the repository, so
you can try the app without retraining them.

Open a terminal in the cloned project folder. Start the backend:

```powershell
uv sync --locked
uv run uvicorn procuresight_ai.api:app
```

Leave that terminal running. Open a second terminal in the same
project folder and start the frontend:

```powershell
npm.cmd --prefix frontend ci
npm.cmd --prefix frontend run dev
```

Open the **Local** link printed by Vite, usually
<http://localhost:5173/>. Click **Analyze order** with the prefilled
example. The compliance score should be **0.0868 (not flagged)**,
and the anomaly score should be **0.5723 (flagged for review)**.

To check input validation, set **Quantity** to `0` and submit again.
The app should show an error and clear the previous results.

If the form loads but scoring fails, check
<http://127.0.0.1:8000/health>. A running backend returns `{"status":"ok"}`.