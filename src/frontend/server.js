const https = require("https");
const http = require("http");
const fs = require("fs");
const express = require("express");
const path = require("path");

const app = express();
const port = parseInt(process.env.PORT || "3000", 10);
const certFile = process.env.SSL_CERT_FILE;
const keyFile = process.env.SSL_KEY_FILE;

// Backend URL from Aspire environment variable (backend runs plain HTTP internally)
const backendUrl = process.env.services__backend__http__0 || "http://localhost:8000";

app.use(express.static(path.join(__dirname, "public")));

// Proxy /api/* to the backend
app.use("/api", (req, res) => {
  const url = new URL(req.url, backendUrl);
  url.pathname = "/api" + url.pathname;

  const options = {
    hostname: url.hostname,
    port: url.port,
    path: url.pathname + url.search,
    method: req.method,
    headers: {
      ...req.headers,
      host: url.host,
    },
  };

  const proxyReq = http.request(options, (proxyRes) => {
    res.writeHead(proxyRes.statusCode, proxyRes.headers);
    proxyRes.pipe(res);
  });

  proxyReq.on("error", (err) => {
    console.error("[Proxy] Error forwarding to backend:", err.message);
    if (!res.headersSent) {
      res.status(502).json({ error: "Backend unavailable", detail: err.message });
    }
  });

  req.pipe(proxyReq);
});

app.get("/", (_req, res) => {
  res.sendFile(path.join(__dirname, "public", "index.html"));
});

const server = https.createServer(
  {
    cert: fs.readFileSync(certFile),
    key: fs.readFileSync(keyFile),
  },
  app
);

server.listen(port, "0.0.0.0", () => {
  console.log(`Frontend listening on https://0.0.0.0:${port}`);
  console.log(`Proxying /api/* to ${backendUrl}`);
});
