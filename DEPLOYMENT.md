# Deployment

SubtypeLab is easiest to publish as one Docker web service. The production Docker image builds the React app, copies the static files into the FastAPI image, and serves the UI plus API from the same public URL.

## Recommended Hackathon Deployment: Render

1. Push this repository to GitHub.
2. In Render, create a new Blueprint from the repository.
3. Render will read `render.yaml` and create one Docker web service named `subtype-lab`.
4. After deploy, use the generated `https://...onrender.com` URL as the project URL.

The service exposes:

- App UI: `/`
- Health check: `/healthz`
- API routes: `/api/...`

No login credentials are required for the demo app.

## Vercel Option

Vercel works well for the frontend only. If you use it, set the Vercel project root to `apps/web`, use `npm run build`, publish `dist`, and set `VITE_API_BASE` to the public backend URL.

For this app, that split deployment is less convenient because the analysis engine is a stateful FastAPI service with Python scientific dependencies and generated reports. A single Docker web service is the safer project-URL path.
