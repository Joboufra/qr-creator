module.exports = {
  apps: [
    {
      name: "qr-frontend",
      script: "./node_modules/next/dist/bin/next",
      args: "start",
      cwd: `${__dirname}/frontend`,
      interpreter: "node",
      env_file: `${__dirname}/.env.frontend`,
      env: {
        NODE_ENV: "production",
        PORT: "3200",
      },
      autorestart: true,
      max_restarts: 5,
      min_uptime: "5s",
    },
  ],
};
