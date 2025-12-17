module.exports = {
  apps: [{
    name: "qr-backend",
    // Usamos bash para expandir variables de entorno definidas en .env
    script: "bash",
    args: [
      "-lc",
      ".venv/bin/uvicorn app.main:app --host ${UVICORN_HOST:-0.0.0.0} --port ${UVICORN_PORT:-8000} --workers ${UVICORN_WORKERS:-2} --proxy-headers"
    ],
    cwd: __dirname,
    interpreter: "none",
    env_file: ".env",
    autorestart: true,
    max_restarts: 5,
    min_uptime: "5s"
  }]
}
