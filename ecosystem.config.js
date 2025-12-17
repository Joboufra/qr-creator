module.exports = {
  apps: [{
    name: "qr-backend",
    script: ".venv/bin/uvicorn",
    args: "__UVICORN_ARGS__",
    cwd: "__APP_CWD__",
    interpreter: "none",
    env_file: ".env",
    autorestart: true
  }]
}
