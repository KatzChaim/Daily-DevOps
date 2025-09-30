

```markdown
# Daily DevOps Dashboard

⚙️ **Daily DevOps** — A FastAPI-based dashboard that delivers:
- 📜 Quote of the Day (משפט היום)  
- 💡 DevOps Tip of the Day  
- 🎥 Curated DevOps Videos  
- 🛠 Recommended Tools  
- 📚 Learning Resources  
- 🔍 Search (DevOps-only content)

UI fully supports Hebrew with RTL design, while comments and code instructions are in English.

---

## 🚀 Features
- **FastAPI backend** with static assets + Jinja2 templates.  
- **Curated content** for DevOps videos, tools, and guides.  
- **Kubernetes-ready** (Deployment, Service, HPA).  
- **CI/CD** with GitHub Actions: build → push image → deploy to AWS EKS.  
- **GHCR (GitHub Container Registry)** hosting for Docker images.  

---

## 🏗 Project Structure

```

Financial-management/
├── Project/
│   ├── main.py           # FastAPI app (entrypoint)
│   ├── content.py        # Curated lists (videos, tools, learning)
│   ├── templates/        # Jinja2 HTML templates
│   ├── static/           # CSS, images, frontend assets
│   └── data/             # JSON files (quotes.json, tips.json)
├── k8s/
│   ├── deployment.yaml   # Kubernetes Deployment
│   ├── service.yaml      # LoadBalancer Service
│   └── hpa.yaml          # Horizontal Pod Autoscaler
├── infra/                # Terraform IaC for VPC + EKS
├── .github/workflows/
│   ├── cd-main.yml       # Build & Deploy workflow
│   └── cd-eks-ghcr.yml   # Alternative deploy workflow
└── README.md             # This file

````

---

## 🖥 Local Development

### 1. Clone repo
```bash
git clone https://github.com/KatzChaim/Financial-management.git
cd Financial-management
````

### 2. Build Docker image

```bash
docker build -t fm-app:local Project
```

### 3. Run locally

```bash
docker run --rm -p 8000:8000 fm-app:local
```

### 4. Test endpoints

```bash
curl http://localhost:8000/healthz
curl http://localhost:8000/
```

Or open [http://localhost:8000/](http://localhost:8000/) in browser.

---

## ☸️ Kubernetes Deployment

### 1. Apply manifests

```bash
kubectl create ns prod
kubectl -n prod apply -f k8s/
```

### 2. Check rollout

```bash
kubectl -n prod get deploy,svc,hpa,pods
```

Service will expose an **AWS ELB hostname** when type=LoadBalancer.

---

## 🔄 CI/CD with GitHub Actions

### Workflow: `.github/workflows/cd-main.yml`

* **On push to `main`**:

  1. Build & push Docker image to GHCR (`latest` + commit SHA).
  2. If `KUBECONFIG_B64` secret exists:

     * Setup `kubectl`
     * Deploy manifests to cluster
     * Rollout updated image pinned to commit SHA.

### Required GitHub Secrets:

* `GITHUB_TOKEN` (default, provided by GitHub)
* `KUBECONFIG_B64` (base64-encoded kubeconfig for your EKS cluster)

> ⚠️ If you prefer AWS IAM keys instead of `KUBECONFIG_B64`, use the workflow `cd-eks-ghcr.yml`.

---

## ☁️ Terraform Infra

Infrastructure is defined in `infra/` using official Terraform AWS modules:

* VPC
* EKS (with managed node groups)

### Basic commands:

```bash
cd infra
terraform init
terraform validate
terraform plan  -var-file=dev.tfvars
terraform apply -var-file=dev.tfvars -auto-approve
```

To destroy resources (save $$):

```bash
terraform destroy -var-file=dev.tfvars -auto-approve
```

---

## 🔍 Search (DevOps-only)

* Search box on UI calls `/search?q=...`.
* Currently matches only curated local content (`content.py`).
* Future enhancement: integrate Google Custom Search API (restricted to DevOps domains).

---

## 📦 Registry & Deployment

Images are stored in:

```
ghcr.io/katzchaim/financial-management
```

Deployed automatically to namespace `prod` in EKS.

---

## 📜 License

MIT — free for personal and commercial use.

```

---

רוצה שאבנה לך גם גרסה **מקוצרת בעברית** של ה־README (בשפה טבעית יותר, למשתמשים לא טכניים), או שנשאיר רק את הגרסה המלאה באנגלית המקצועית?
```
