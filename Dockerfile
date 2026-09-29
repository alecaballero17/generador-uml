# Imagen única: FastAPI expone la API y sirve el editor web estático.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app

# El OCR del servidor usa pytesseract; Tesseract y el idioma español deben
# existir también en la imagen desplegada, no solamente en el equipo local.
RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-spa \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY backend ./backend
COPY frontend ./frontend
RUN mkdir -p /app/output

EXPOSE 8080

# Cloud Run proporciona PORT; el valor 8080 permite probar el contenedor localmente.
CMD ["sh", "-c", "exec uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
