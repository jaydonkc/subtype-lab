# Technical Steering

Use a local-first architecture:

- Python + FastAPI for the analysis engine.
- React + TypeScript + Vite for the web UI.
- Deterministic NumPy/Pandas analysis functions for the MVP.
- Local artifacts written under `artifacts/`.
- Docker Compose as the judge-friendly startup path.

Keep the app runnable without external API keys or cloud services. The synthetic demo dataset is the default path for demos and tests.
