var builder = DistributedApplication.CreateBuilder(args);

var certPath = Path.GetFullPath(Path.Combine(builder.AppHostDirectory, "..", "..", "tmp", "localhost.crt"));
var keyPath = Path.GetFullPath(Path.Combine(builder.AppHostDirectory, "..", "..", "tmp", "localhost.key"));

var backend = builder.AddPythonApp("backend", "../backend", "main.py")
    .WithHttpsEndpoint(env: "PORT")
    .WithExternalHttpEndpoints()
    .WithEnvironment("SSL_CERT_FILE", certPath)
    .WithEnvironment("SSL_KEY_FILE", keyPath);

var frontend = builder.AddNpmApp("frontend", "../frontend")
    .WithReference(backend)
    .WaitFor(backend)
    .WithHttpsEndpoint(env: "PORT")
    .WithExternalHttpEndpoints()
    .WithEnvironment("SSL_CERT_FILE", certPath)
    .WithEnvironment("SSL_KEY_FILE", keyPath);

builder.Build().Run();
