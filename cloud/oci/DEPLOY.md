# Host the Saylacian model API on Oracle Cloud

This deploys the project's existing models as a small HTTPS API. It avoids an external provider's per-request quota; it does not give unlimited compute. A free VM has finite speed, and Oracle account eligibility, home-region capacity, and its Always Free conditions apply.

## 1. Create a VM

Create an Oracle Cloud account and an Always Free Ampere A1 VM (at least 2 OCPUs and 12 GB RAM if available), using Ubuntu 24.04 ARM64. Configure a static public IP, DNS A record, and ingress TCP ports 22, 80, and 443. Leave port 8080 private. Oracle may show out-of-capacity in some home regions. Account signup and VM provisioning require your Oracle account; this repository cannot create the cloud account or deploy into it.

## 2. Install Docker and get the source

Install Docker Engine and the Docker Compose plugin for Ubuntu using Docker's official instructions. Then clone or copy this Saylacian source tree to the VM. Build downloads roughly 744 MB of model assets and verifies each file against the pinned project manifests.

## 3. Configure the endpoint

From the project root on the VM:

```bash
cd cloud/oci
cp .env.example .env
```

Set `SAYLACIAN_DOMAIN` to the DNS name pointed at the VM. Create a unique long API token and put it in `SAYLACIAN_SERVICE_TOKEN`. Protect the `.env` file (`chmod 600 .env`). Start the API:

```bash
docker compose up -d --build
docker compose logs -f
```

Caddy obtains and renews HTTPS certificates automatically when DNS and ports 80/443 are reachable. Check `https://your-domain.example/health` for `{"ok":true,...}`. Do not expose port 8080 publicly.

## 4. Connect Saylacian

In the PowerShell session used to launch Saylacian:

```powershell
$env:SAYLACIAN_TRANSLATION_URL = "https://your-domain.example"
$env:SAYLACIAN_SERVICE_TOKEN = Read-Host "Saylacian server token"
cd "<PROJECT_ROOT>"
.\.venv\Scripts\python.exe main.py
```

Automatic provider mode tries this server, then Cloudflare, then local models. To require this server, set `$env:SAYLACIAN_TRANSLATION_PROVIDER = "selfhosted"` before starting the app.

## Deployment and scale limits

- The service accepts English, French and Somali Latin, up to 4,000 characters per request. Somali/French uses the existing experimental English pivot.
- It requires a bearer token, caps the active request threads at 16 and concurrent model runs at 2, and returns 503 when its translation wait queue is full.
- The API sends text over HTTPS to your VM. The service logs HTTP metadata but not text or the token.
- Do not bundle one shared API token in a public app: it can be extracted. Public distribution needs user authentication/API gateway credentials and abuse monitoring.
- Oracle's Always Free VM allocation is fixed and capacity is not guaranteed. Benchmark with real traffic; add sponsored or paid servers before public high-volume launch. “No per-request quota” means no provider charge per translation, not limitless users or uptime.
- Cloudflare fallback still has its separate daily free limit. Local models continue to work without network.

## Stop the service

```bash
docker compose down
```

The Caddy certificate volumes remain on disk. Remove them only if you intend to discard the saved certificates.
