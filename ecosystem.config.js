module.exports = {
  apps: [
    {
      name: "qr-frontend",
      script: "npm",
      args: "start",
      cwd: `${__dirname}/frontend`,
      interpreter: "none",
      env_file: `${__dirname}/.env.frontend`,
      env: {
        NODE_ENV: "production",
      },
      autorestart: true,
      max_restarts: 5,
      min_uptime: "5s",
    },
  ],
};
