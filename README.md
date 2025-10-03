```markdown
# Daily-DevOps 🚀

A small DevOps dashboard: **Quote of the Day**, **Tip of the Day**, a **video carousel** with arrows, **recommended tools**, **learning links**, and **DevOps-focused search** (local + web with allow-listed domains).  
Built with **FastAPI**, containerized with **Docker**, deployed on **Kubernetes (AWS EKS)**, infra via **Terraform**, and **CI/CD** using **GitHub Actions**.

**English | [עברית](./README.he.md)**

---

## What this project does (in two lines)
- Serves a daily DevOps dashboard (+ curated search).
- Ships a CI → build & push to GHCR → CD to EKS, pinning image to `GITHUB_SHA`.

---

## Repository layout
```

Project/
├─ app/
│  ├─ main.py                # FastAPI app & APIs
│  ├─ content.py             # curated videos/tools/learning
│  ├─ search_config.py       # allow-listed domains + query suffix
│  ├─ templates/index.html   # Jinja2 template
│  ├─ static/                # style.css, addons.css, icons/favicon.svg
│  └─ data/                  # quotes.json, tips.json, ideas.json (created by API)
├─ k8s/                      # Kubernetes manifests
│  ├─ deployment.yaml
│  ├─ service.yaml
│  └─ hpa.yaml (optional)
├─ infra/                    # Terraform (VPC + EKS)
└─ .github/workflows/        # CI/CD

````

---

## Prerequisites
- Python 3.11+ / Docker 24+
- kubectl 1.28+ / AWS CLI 2.9+
- Terraform 1.6+ (if provisioning infra)

---

## Run locally (5 minutes)
```bash
cd Project
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# http://localhost:8000   (health: /healthz)
````

### With Docker

```bash
cd Project
docker build -t daily-devops:local .
docker run --rm -p 8000:8000 daily-devops:local
```

---

## Update content

* Quotes/Tips: `Project/app/data/quotes.json`, `tips.json`
* Videos/Tools/Learning: `Project/app/content.py`
* Web search allow-list: `Project/app/search_config.py`

  * `ALLOWED_DOMAINS` — trusted domains (kubernetes.io, docker.com, docs.github.com, …)
  * `QUERY_SUFFIX` — extra query text (e.g. `"devops tutorial"`)

---

## Kubernetes (EKS) deployment

### 1) Provision infra (optional)

```bash
cd infra
terraform init
terraform apply -var-file=dev.tfvars -auto-approve
```

### 2) Connect to EKS

```bash
aws eks update-kubeconfig --name <EKS_CLUSTER_NAME> --region <AWS_REGION>
kubectl get nodes
```

### 3) Apply manifests

```bash
kubectl create ns prod 2>/dev/null || true
kubectl -n prod apply -f k8s/
kubectl -n prod rollout status deploy/fm-app
kubectl -n prod get svc fm-svc -w   # wait for EXTERNAL-IP
```

> Ensure `k8s/deployment.yaml`’s `image:` points to your GHCR path:
> `ghcr.io/<owner>/<repo>:<tag>`

---

## CI/CD (GitHub Actions)

**What happens**

* Build & push image to GHCR with tags `latest` and `${GITHUB_SHA}`
* CD: update Deployment to `${GITHUB_SHA}` and wait for rollout

**Required Secrets/Vars**

| Name                                          | Kind       | Used for                         |
| --------------------------------------------- | ---------- | -------------------------------- |
| `AWS_REGION`                                  | Var/Secret | AWS region (e.g. `eu-central-1`) |
| `EKS_CLUSTER_NAME`                            | Var/Secret | EKS cluster name (e.g. `fm-eks`) |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | Secret     | if not using OIDC                |
| `KUBECONFIG_B64`                              | Secret     | optional — CD via kubeconfig     |

> Recommended: OIDC (IAM Role with GitHub trust) instead of long-lived keys.

---

## Frontend notes

* RTL by default; English blocks use `.ltr`.
* Quote/Tip/Video use **round arrows** (RTL-aware) defined in `static/addons.css`.
* “Have an idea?” modal persists to `app/data/ideas.json`.

---

## Quick checks

```bash
curl http://<LB-DNS>/healthz
kubectl -n prod logs deploy/fm-app
kubectl -n prod get deploy,svc,ingress
```

---

## Troubleshooting

* **ImagePullBackOff** — verify image exists and path is correct (`ghcr.io/<owner>/<repo>:<tag>`). For private GHCR add `imagePullSecret`.
* **No EXTERNAL-IP** — ensure `type: LoadBalancer`, public subnets, and AWS LB controller/permissions.
* **"You must be logged in to the server"** — refresh kubeconfig/permissions (or OIDC).
* **404 for quotes/tips** — ensure JSON files exist under `app/data`.

---

## Clean-up & costs

EKS/NAT/LB incur costs. When done:

```bash
cd infra
terraform destroy -var-file=dev.tfvars -auto-approve
```

### Clean up old GHCR images

Create a scheduled workflow:

```yaml
# .github/workflows/ghcr-cleanup.yml
name: Cleanup GHCR
on:
  workflow_dispatch:
  schedule:
    - cron: "0 3 * * 0"   # weekly

jobs:
  cleanup:
    runs-on: ubuntu-latest
    permissions:
      packages: write
      contents: read
    steps:
      - uses: actions/delete-package-versions@v5
        with:
          package-type: "container"
          package-name: "${{ github.repository }}"   # usually <owner>/<repo>
          min-versions-to-keep: 15
          delete-only-untagged-versions: true
```

### Local Docker cleanup

```bash
docker image prune -a
docker system prune -a --volumes
```

---

## Screenshots

Place images under `docs/images/` and keep filenames short. Example:

```
docs/images/
├─ 01-home.png
├─ 02-search.png
└─ 03-ideas-modal.png
```

Embed them here:

![Home](./docs/images/01-home.png)
![Search](./docs/images/02-search.png)
![Ideas modal](./docs/images/03-ideas-modal.png)

