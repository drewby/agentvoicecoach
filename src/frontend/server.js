const https = require("https");
const fs = require("fs");
const express = require("express");
const path = require("path");

const app = express();
const port = parseInt(process.env.PORT || "3000", 10);
const certFile = process.env.SSL_CERT_FILE;
const keyFile = process.env.SSL_KEY_FILE;

app.use(express.static(path.join(__dirname, "public")));

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
});
