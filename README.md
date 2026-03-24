# PostForge

**Instagram Content Automation Engine**
Internal tool for automated generation of Instagram posts — built for Confluex, designed to be reusable across brands.

---

## Overview

PostForge automates the full Instagram content creation pipeline:

1. Receive input (image, idea, topic, or campaign type)
2. Analyze and classify the content
3. Generate copy (title, hook, caption, CTA, hashtags) via Claude AI
4. Generate a 1080x1080 post image with brand theming via Pillow
5. Persist all outputs (image, captions, metadata)
6. Provide a review interface for manual approval before publishing

---

## Stack

| Layer | Technology |
|---|---|
| API | FastAPI + Uvicorn |
| AI — Copy | Anthropic Claude API |
| Image Rendering | Pillow (PIL) |
| Database | SQLite + SQLAlchemy |
| File Watcher | Watchdog |
| Review UI | Jinja2 + HTML |
| Container | Docker + Compose |
| Config | Pydantic Settings + .env |

---

## Project Structure

```
postforge/
├── app/
│   ├── main.py              # FastAPI app, lifespan, routing
│   ├── config.py            # Settings (Pydantic + .env)
│   ├── database.py          # SQLAlchemy setup
│   ├── models/              # SQLAlchemy ORM models
│   ├── schemas/             # Pydantic request/response schemas
│   ├── routers/             # API route handlers
│   ├── services/            # Core business logic
│   │   ├── input_processor  # Input analysis & classification
│   │   ├── copy_generator   # Claude API copy generation
│   │   ├── image_generator  # Pillow image rendering
│   │   ├── job_manager      # Pipeline orchestration
│   │   ├── file_manager     # Output file organization
│   │   └── watcher          # Inbox directory monitor
│   ├── integrations/        # External API stubs (Instagram, Canva, Drive)
│   └── templates/           # Jinja2 HTML review interface
├── config/brands/           # Brand configuration JSON files
├── assets/                  # Brand logos and static assets
├── fonts/                   # Custom TrueType fonts
├── input/inbox/             # Drop files here for auto-processing
├── input/processed/         # Processed input files
├── output/final_posts/      # Generated post images
├── output/captions/         # Generated copy (JSON + TXT)
├── output/metadata/         # Job metadata
└── output/logs/             # Application logs
```

---

## Quick Start

### 1. Clone and set up environment

```bash
cd postforge
cp .env.example .env
```

Edit `.env` and add your Anthropic API key:
```
ANTHROPIC_API_KEY=sk-ant-...your-key...
```

### 2. Install dependencies

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Run locally

```bash
python run.py
```

The app starts at `http://localhost:8000`

- **Review Dashboard** → `http://localhost:8000/review`
- **API Docs** → `http://localhost:8000/docs`
- **Health Check** → `http://localhost:8000/health`

---

## Usage

### Option A — Web Dashboard

Open `http://localhost:8000/review` and use the "Crear nuevo post" form at the top.

### Option B — Drop a file in the inbox

Drop any `.jpg`, `.png`, or `.txt` file into `input/inbox/` — the watcher auto-creates and processes a job.

### Option C — REST API

**Create a text-based job:**
```bash
curl -X POST http://localhost:8000/jobs/ \
  -F "input_type=text" \
  -F "input_text=Automatizamos tu marketing digital con IA" \
  -F "campaign_type=service_promo" \
  -F "brand_id=confluex"
```

**Upload an image:**
```bash
curl -X POST http://localhost:8000/jobs/ \
  -F "input_type=image" \
  -F "image=@/path/to/photo.jpg" \
  -F "brand_id=confluex"
```

**Check job status:**
```bash
curl http://localhost:8000/jobs/{job_id}
```

**Download generated image:**
```bash
curl -o post.png http://localhost:8000/jobs/{job_id}/image
```

**Approve for publishing:**
```bash
curl -X POST http://localhost:8000/jobs/{job_id}/approve
```

---

## Adding a New Brand

1. Create `config/brands/your-brand.json` (copy `confluex.json` as template)
2. Call the seed endpoint:
   ```bash
   curl -X POST http://localhost:8000/brands/seed
   ```
3. Use `brand_id=your-brand` when creating jobs

Key brand config fields:
```json
{
  "id": "mybrand",
  "name": "My Brand",
  "visual_identity": { "primary_color": "#...", "accent_color": "#..." },
  "voice": { "tone": "...", "language": "es" },
  "content": { "base_hashtags": [...], "cta_options": [...] },
  "brand_assets": { "instagram_handle": "@...", "website": "..." }
}
```

---

## Image Templates

PostForge includes 3 built-in Pillow templates:

| Template | Description |
|---|---|
| `gradient_text` | Gradient background + semi-transparent dark panel + text |
| `dark_tech` | Deep dark background + tech grid + glowing accents |
| `split_layout` | Left color panel / Right content area |
| `photo_overlay` | Input image as background + dark gradient overlay |

Template is auto-selected based on input type (images → `photo_overlay`, text → random tech template).

**Custom fonts:** Drop `.ttf` files into `fonts/` named `Bold.ttf` / `Regular.ttf` and they'll be loaded automatically.

---

## Docker

```bash
# Build and run
docker compose up --build

# Run in background
docker compose up -d

# Logs
docker compose logs -f postforge
```

---

## Job Lifecycle

```
PENDING → ANALYZING → GENERATING_COPY → GENERATING_IMAGE → REVIEW → APPROVED → PUBLISHED
                                                                              ↑
                                                                         FAILED (on error)
```

- Jobs in **REVIEW** status await manual approval in the dashboard
- **APPROVED** jobs are ready to publish to Instagram
- **PUBLISHED** = posted via Meta Graph API (stub in MVP)

---

## Running Tests

```bash
pytest tests/ -v
```

---

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `ANTHROPIC_API_KEY` | Claude API key (required for copy gen) | — |
| `ANTHROPIC_MODEL` | Claude model to use | `claude-sonnet-4-6` |
| `DEFAULT_BRAND` | Default brand ID for jobs | `confluex` |
| `WATCHER_ENABLED` | Auto-monitor inbox folder | `true` |
| `APP_ENV` | `development` or `production` | `development` |
| `DATABASE_URL` | SQLAlchemy DB URL | `sqlite:///./postforge.db` |
| `INSTAGRAM_ACCESS_TOKEN` | Meta Graph API token (future) | — |

---

## Roadmap — Future Integrations

### Phase 4 — Publishing Automation
- [ ] **Meta Graph API** — direct publish to Instagram Business account
- [ ] **Content Scheduler** — queue posts for specific times (APScheduler or Celery)

### Phase 5 — Design Expansion
- [ ] **Canva Connect API** — use Canva templates with autofill
- [ ] **Custom font uploads** via API
- [ ] **Multi-slide carousel** generation

### Phase 6 — Cloud & Collaboration
- [ ] **Google Drive** sync — auto-upload outputs to a shared Drive folder
- [ ] **Multi-user support** — user accounts with brand permissions
- [ ] **Webhook support** — trigger jobs from external systems

### Phase 7 — Analytics & Optimization
- [ ] **Performance tracking** — connect published posts to analytics
- [ ] **A/B copy variants** — generate multiple copy options per job
- [ ] **WhatsApp Business** — send review notifications via Twilio

---

## Architecture Decisions

- **SQLite** is used for MVP simplicity. Swap `DATABASE_URL` to Postgres for production scale.
- **Background tasks** (FastAPI `BackgroundTasks`) handle job processing asynchronously so the API returns immediately.
- **Brand config** lives in JSON files (`config/brands/`) and is also synced to DB — source of truth is the JSON file.
- **Pillow** is used instead of Canva for the MVP renderer to avoid external API dependency. The `integrations/canva.py` stub is ready for future integration.
- **Watchdog** runs in a daemon thread and is lifecycle-managed by FastAPI's lifespan context.

---

Built by Confluex · PostForge v1.0.0
