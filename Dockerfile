FROM node:20-bookworm-slim AS frontend-deps

WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

FROM node:20-bookworm-slim AS frontend-builder

WORKDIR /app/frontend

COPY --from=frontend-deps /app/frontend/node_modules ./node_modules
COPY frontend ./

ARG NEXT_PUBLIC_API_URL=
ARG NEXT_PUBLIC_RAZORPAY_KEY_ID=

ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_RAZORPAY_KEY_ID=$NEXT_PUBLIC_RAZORPAY_KEY_ID

RUN npm run build

FROM node:20-bookworm-slim AS runner

ENV APP_ENV=production \
    DEBUG=false \
    DATABASE_URL=sqlite:////data/spaceiq.db \
    FRONTEND_URL=http://localhost:7860 \
    ALLOWED_ORIGINS=http://localhost:7860 \
    NEXT_PUBLIC_API_URL= \
    PORT=7860 \
    PYTHONUNBUFFERED=1 \
    PATH=/opt/venv/bin:$PATH

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-venv nginx ca-certificates curl \
    && rm -rf /var/lib/apt/lists/* \
    && python3 -m venv /opt/venv

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

COPY backend /app/backend
COPY --from=frontend-builder /app/frontend /app/frontend
COPY deploy/huggingface/nginx.conf /etc/nginx/nginx.conf
COPY deploy/huggingface/start.sh /app/start.sh

RUN mkdir -p /data /var/log/nginx /var/lib/nginx/body \
    && chmod +x /app/start.sh

EXPOSE 7860

CMD ["/app/start.sh"]
