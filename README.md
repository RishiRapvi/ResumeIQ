# ResumeIQ

ResumeIQ is a Flask-based resume review app that uses Anthropic's Claude API to analyze PDF resumes and return structured feedback, including an overall score, ATS score, missing keywords, strengths, weaknesses, and concrete suggestions.

## What is included

- A Flask backend that serves the UI and handles resume analysis
- A polished frontend for drag-and-drop PDF uploads
- A built-in demo mode so recruiters can preview the product without uploading a resume
- Better validation and error handling than the original standalone files
- A VS Code launch configuration for local development

## Project structure

- `app.py` - Flask app and analysis API
- `templates/index.html` - frontend UI
- `requirements.txt` - Python dependencies
- `render.yaml` - Render deployment blueprint
- `gunicorn.conf.py` - production web server config
- `.env.example` - environment variable template
- `.vscode/launch.json` - debug profile for VS Code

## Setup

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

4. Add your Anthropic API key to `.env`.

## Run locally

```bash
python app.py
```

Then open [http://localhost:5000](http://localhost:5000).

Recruiter-friendly preview:

- Click `Try Demo Mode` on the landing page to load a sample analysis instantly.
- This works without uploading a PDF and without setting `ANTHROPIC_API_KEY`.

## Deploy to a public domain

This repo is set up for Render, which can give you:

- an immediate public `onrender.com` URL
- optional connection to your own custom domain
- automatic HTTPS

### 1. Push this repo to GitHub

If it is not already pushed, commit your changes and push the repository to GitHub.

### 2. Create the Render web service

1. Sign in to Render.
2. Create a new Blueprint or Web Service from your GitHub repo.
3. If you use the Blueprint in `render.yaml`, Render will pick up:
   - build command: `pip install -r requirements.txt`
   - start command: `gunicorn app:app -c gunicorn.conf.py`
   - health check path: `/api/health`
4. Set `ANTHROPIC_API_KEY` in Render when prompted.

### 3. Use the public URL

After deployment, Render will assign a public `*.onrender.com` domain to your app.

### 4. Connect your own custom domain

If you already own a domain:

1. Open your Render service.
2. Go to the custom domain settings.
3. Add your domain.
4. Copy the DNS records Render gives you into your DNS provider.
5. Wait for verification and SSL issuance.

## Production notes

- Render requires your service to bind to `0.0.0.0` on the `PORT` environment variable. This repo handles that through `gunicorn.conf.py`.
- `ProxyFix` is enabled so Flask behaves correctly behind Render's HTTPS proxy.
- Render can keep the generated `onrender.com` domain even if you later add your own custom domain.

## Run tests

```bash
python -m unittest discover -s tests
```

## Environment variables

- `ANTHROPIC_API_KEY` - required
- `ANTHROPIC_MODEL` - optional, defaults to `claude-sonnet-4-20250514`
- `FLASK_DEBUG` - optional, set to `1` for debug mode
- `PORT` - optional, defaults to `5000`

## Notes

- The app accepts PDF uploads only.
- Frontend and backend now run from the same Flask project, so extra CORS setup is no longer needed.
- The provided `archive.zip` was not integrated because it contains an unrelated image dataset and is not used by this resume app.
