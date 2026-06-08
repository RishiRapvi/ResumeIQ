# ResumeIQ

ResumeIQ is a Flask-based resume review app that uses Anthropic's Claude API to analyze PDF resumes and return structured feedback, including an overall score, ATS score, missing keywords, strengths, weaknesses, and concrete suggestions.

## What this project includes

- A Flask backend that serves the UI and handles resume analysis
- A recruiter-friendly frontend for drag-and-drop PDF uploads
- A built-in demo mode so visitors can preview the product without uploading a resume
- A sample resume page to make the demo output easy to understand
- A static GitHub Pages build for free public sharing
- Render deployment files for the full backend version
- Tests and basic error handling for local and deploy workflows

## Project structure

- `app.py` - Flask app and analysis API
- `templates/index.html` - main product landing page and demo UI
- `templates/sample_resume.html` - sample resume shown with demo mode
- `scripts/build_github_pages.py` - static export builder for GitHub Pages
- `docs/` - generated static site for GitHub Pages publishing
- `tests/test_app.py` - smoke tests for app routes and static export
- `requirements.txt` - Python dependencies
- `render.yaml` - Render deployment blueprint
- `gunicorn.conf.py` - production web server config
- `.env.example` - environment variable template
- `.vscode/launch.json` - VS Code debug profile
- `.vscode/settings.json` - VS Code workspace defaults for `.env` loading

## Local setup

1. Create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a local env file:

```bash
cp .env.example .env
```

4. Add your Anthropic API key to `.env` if you want live resume analysis.

## Run locally

```bash
python app.py
```

Then open [http://127.0.0.1:5050](http://127.0.0.1:5050).

Why `127.0.0.1:5050` instead of `localhost:5000`:

- On some macOS setups, `localhost:5000` can resolve to another local service instead of this Flask app.
- This project now defaults to port `5050` locally to avoid that confusion.

Recruiter-friendly preview:

- Click `Try Demo Mode` on the landing page to load a sample analysis instantly.
- Click `View Sample Resume` to inspect the artifact being analyzed.
- Demo mode works without uploading a PDF and without setting `ANTHROPIC_API_KEY`.

## Environment variables

- `ANTHROPIC_API_KEY` - required for live analysis
- `ANTHROPIC_MODEL` - optional, defaults to `claude-sonnet-4-20250514`
- `FLASK_DEBUG` - optional, set to `1` for debug mode
- `PORT` - optional, defaults to `5050` locally

## Run tests

```bash
python -m unittest discover -s tests
```

## Publish free on GitHub Pages

This repo supports a zero-cost static recruiter demo on GitHub Pages.

### Build the Pages site

```bash
python scripts/build_github_pages.py
```

That command regenerates the static site in `docs/`.

### What the GitHub Pages version includes

- The recruiter-focused homepage
- Working demo mode directly in the browser
- The sample resume page
- Your GitHub and LinkedIn links

### What the GitHub Pages version does not include

- Live PDF upload analysis
- Flask API routes
- Anthropic-backed resume processing

GitHub Pages is being used here as a polished static showcase. The full backend implementation stays in the Flask app and source code.

### Enable GitHub Pages

1. Push the repo to GitHub.
2. In the repository, go to `Settings` -> `Pages`.
3. Under `Build and deployment`, choose `Deploy from a branch`.
4. Select the `main` branch and the `/docs` folder.
5. Click `Save` and wait for GitHub to publish the site.

Your public URL will be:

- `https://rishirapvi.github.io/ResumeIQ/`

### GitHub Pages troubleshooting

- If you see a GitHub 404 page, Pages is usually not enabled yet or the wrong source folder is selected.
- For this repo, the source must be `main` plus `/docs`.
- Use the repo URL path, not just your profile root:
  - correct: `https://rishirapvi.github.io/ResumeIQ/`
  - wrong: `https://rishirapvi.github.io/`
- If you update `templates/`, rerun `python scripts/build_github_pages.py` before pushing.

## Deploy the full app publicly

This repo is also set up for Render, which can give you:

- a public `onrender.com` URL
- optional connection to your own custom domain
- automatic HTTPS

### Render setup

1. Push this repo to GitHub.
2. Sign in to Render.
3. Create a new Blueprint or Web Service from this repository.
4. If you use `render.yaml`, Render will pick up:
   - build command: `pip install -r requirements.txt`
   - start command: `gunicorn app:app -c gunicorn.conf.py`
   - health check path: `/api/health`
5. Set `ANTHROPIC_API_KEY` in Render when prompted.

After deployment, Render will assign a public `*.onrender.com` domain to your app.

## Production notes

- Render requires your service to bind to `0.0.0.0` on the `PORT` environment variable. This repo handles that through `gunicorn.conf.py`.
- `ProxyFix` is enabled so Flask behaves correctly behind a proxy or HTTPS terminator.
- Frontend and backend run from the same Flask project, so extra CORS setup is not needed.

## Notes

- The app accepts PDF uploads only.
- The provided `archive.zip` was not integrated because it contains an unrelated image dataset and is not used by this resume app.
