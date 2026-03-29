# ── Base image ──────────────────────────────────────────────────────────────
FROM python:3.12-slim

# ── System deps ─────────────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ── Install uv ──────────────────────────────────────────────────────────────
RUN pip install uv

# ── App directory ───────────────────────────────────────────────────────────
WORKDIR /app

# ── Dependencias (cacheadas si no cambia pyproject.toml) ────────────────────
COPY pyproject.toml uv.lock* ./

RUN uv sync --group dev

# ── Código fuente ───────────────────────────────────────────────────────────
COPY . .

# ── Puerto ──────────────────────────────────────────────────────────────────
ENV PORT=5000
EXPOSE ${PORT}

# ── Arranque ────────────────────────────────────────────────────────────────
CMD uv run gunicorn "server:init_webapp('./config/dev.config')" \
    --bind 0.0.0.0:${PORT} \
    --workers 4
