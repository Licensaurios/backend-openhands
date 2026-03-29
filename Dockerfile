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

# ── Copiar todo el proyecto ──────────────────────────────────────────────────
# Se copia todo junto porque setuptools necesita server/ y README.md
# para poder instalar el paquete como editable durante uv sync
COPY . .

# ── Instalar dependencias ────────────────────────────────────────────────────
RUN uv sync --group dev

# ── Puerto ──────────────────────────────────────────────────────────────────
ENV PORT=5000
EXPOSE ${PORT}

# ── Arranque ────────────────────────────────────────────────────────────────
CMD uv run gunicorn "server:init_webapp('./config/dev.config')" \
    --bind 0.0.0.0:${PORT} \
    --workers 4
