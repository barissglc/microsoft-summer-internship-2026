# Sadece API. Arayüz (frontend/dist) sunucuda Nginx tarafından doğrudan sunulur.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MALLOC_ARENA_MAX=2

WORKDIR /app
COPY backend/app ./app

USER nobody
EXPOSE 8000

CMD ["python", "-m", "app.main"]
