# ============================================
# DOCKERFILE - OPORTUNIDADBOT (DÍA 4)
# Multi-stage build para imagen optimizada
# ============================================

# ====== ETAPA 1: BUILDER ======
FROM python:3.11-slim as builder

WORKDIR /app

# Instalar dependencias de compilación
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libxml2-dev \
    libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primero (para cachear)
COPY requirements.txt .

# Instalar dependencias en una carpeta temporal
RUN pip install --no-cache-dir --user -r requirements.txt

# ====== ETAPA 2: FINAL ======
FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias de runtime (solo las necesarias)
RUN apt-get update && apt-get install -y \
    libxml2 \
    libxslt1.1 \
    && rm -rf /var/lib/apt/lists/*

# Copiar dependencias desde builder
COPY --from=builder /root/.local /root/.local

# Asegurar que las dependencias estén en PATH
ENV PATH=/root/.local/bin:$PATH

# Copiar código fuente
COPY . .

# Variables de entorno
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Puerto de la aplicación
EXPOSE 8000

# Comando de inicio
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]