var builder = DistributedApplication.CreateBuilder(args);

// Load .env file from repo root if it exists (Python-style env file)
var envFile = Path.GetFullPath(Path.Combine(builder.AppHostDirectory, "..", "..", ".env"));
if (File.Exists(envFile))
{
    foreach (var line in File.ReadAllLines(envFile))
    {
        var trimmed = line.Trim();
        if (string.IsNullOrEmpty(trimmed) || trimmed.StartsWith('#')) continue;
        var eqIndex = trimmed.IndexOf('=');
        if (eqIndex <= 0) continue;
        var key = trimmed[..eqIndex].Trim();
        var value = trimmed[(eqIndex + 1)..].Trim();
        Environment.SetEnvironmentVariable(key, value);
    }
}

var certPath = Path.GetFullPath(Path.Combine(builder.AppHostDirectory, "..", "..", "tmp", "localhost.crt"));
var keyPath = Path.GetFullPath(Path.Combine(builder.AppHostDirectory, "..", "..", "tmp", "localhost.key"));

var backend = builder.AddPythonApp("backend", "../backend", "main.py", "../backend/.venv")
    .WithHttpEndpoint(env: "PORT")
    .WithExternalHttpEndpoints()
    .WithEnvironment("VB_API_KEY", Environment.GetEnvironmentVariable("VB_API_KEY") ?? "")
    .WithEnvironment("VB_SIM_API_KEY", Environment.GetEnvironmentVariable("VB_SIM_API_KEY") ?? "")
    .WithEnvironment("VB_COACH_API_KEY", Environment.GetEnvironmentVariable("VB_COACH_API_KEY") ?? "")
    .WithEnvironment("OPENAI_API_KEY", Environment.GetEnvironmentVariable("OPENAI_API_KEY") ?? "");

// The OTLP HTTP endpoint is configured in launchSettings.json and enables
// the Aspire dashboard to accept OTLP/HTTP (protobuf/JSON) alongside gRPC.
// The frontend proxy needs this separate endpoint for browser trace forwarding.
var otlpHttpEndpoint = Environment.GetEnvironmentVariable("ASPIRE_DASHBOARD_OTLP_HTTP_ENDPOINT_URL") ?? "";

var frontend = builder.AddNpmApp("frontend", "../frontend")
    .WithReference(backend)
    .WaitFor(backend)
    .WithHttpsEndpoint(env: "PORT")
    .WithExternalHttpEndpoints()
    .WithEnvironment("SSL_CERT_FILE", certPath)
    .WithEnvironment("SSL_KEY_FILE", keyPath)
    .WithEnvironment("OTEL_EXPORTER_OTLP_HTTP_ENDPOINT", otlpHttpEndpoint);

builder.Build().Run();
