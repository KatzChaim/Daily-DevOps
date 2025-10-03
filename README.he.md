# Daily-DevOps 🚀

דשבורד DevOps בעברית:
**משפט היום**, **טיפ היום**, **וידאו (עם חיצים)**, **כלים מומלצים**, **קישורי לימוד**, וחיפוש DevOps (מקומי + אינטרנט עם סינון דומיינים).
נבנה ב-**FastAPI**, נעטף ב-**Docker**, נפרס על **Kubernetes (AWS EKS)**, מנוהל כ-**Terraform**, עם **CI/CD** ב-**GitHub Actions**.

---

## מה הפרויקט עושה (ב-2 שורות)

* מספק אתר סטטי-דינמי קטן לצפייה יומית בתוכן DevOps + חיפוש ממוקד.
* כולל תהליך Build → Push ל-GHCR → Deploy ל-EKS (צמידות ל-`GITHUB_SHA`).

---

## מבנה התיקיות

```
Project/
├─ app/
│  ├─ main.py                # שרת FastAPI וה-API
│  ├─ content.py             # רשימות: סרטונים/כלים/לימוד
│  ├─ search_config.py       # דומיינים מאושרים + סיומת חיפוש
│  ├─ templates/index.html   # תבנית הדף
│  ├─ static/                # style.css, addons.css, icons/favicon.svg
│  └─ data/                  # quotes.json, tips.json, ideas.json (נוצר אוטומטית)
├─ k8s/                      # מניפסטים לפריסה
│  ├─ deployment.yaml
│  ├─ service.yaml
│  └─ hpa.yaml (אופציונלי)
├─ infra/                    # Terraform (VPC + EKS)
└─ .github/workflows/        # CI/CD
```

---

## דרישות

* Python 3.11+ / Docker 24+
* kubectl 1.28+ / AWS CLI 2.9+
* Terraform 1.6+ (אם מקימים תשתית)

---

## הרצה מקומית (5 דקות)

```bash
cd Project
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# http://localhost:8000  (בריאות: /healthz)
```

### Docker (ללא פייתון מקומי)

```bash
cd Project
docker build -t daily-devops:local .
docker run --rm -p 8000:8000 daily-devops:local
```

---

## עדכון תוכן

* ציטוטים/טיפים: `Project/app/data/quotes.json`, `tips.json`
* סרטונים/כלים/קישורים: `Project/app/content.py`
* חיפוש באינטרנט: `Project/app/search_config.py`

  * `ALLOWED_DOMAINS` – רשימת דומיינים מאושרים (kubernetes.io, docker.com, docs.github.com, וכו’)
  * `QUERY_SUFFIX` – סיומת לשאילתה (למשל: `"devops tutorial"`)

---

## פריסה ל-Kubernetes (EKS)

### 1) תשתית (אופציונלי, אם אין EKS)

```bash
cd infra
terraform init
terraform apply -var-file=dev.tfvars -auto-approve
```

### 2) התחברות לקלאסטר

```bash
aws eks update-kubeconfig --name <EKS_CLUSTER_NAME> --region <AWS_REGION>
kubectl get nodes
```

### 3) פריסה

```bash
kubectl create ns prod 2>/dev/null || true
kubectl -n prod apply -f k8s/
kubectl -n prod rollout status deploy/fm-app
kubectl -n prod get svc fm-svc -w   # המתנה ל-EXTERNAL-IP
```

> **חשוב**: ודאו שב-`k8s/deployment.yaml` השדה `image:` מצביע ל-GHCR שלכם, למשל:
> `ghcr.io/<owner>/<repo>:<tag>`

---

## CI/CD (GitHub Actions)

### מה קורה?

* **Build & Push** תמונה ל-GHCR עם תגיות `latest` ו-`${GITHUB_SHA}`
* **CD**: עדכון ה-Deployment ל-`${GITHUB_SHA}` ו-Rollout

### Secrets/Vars נחוצים

| שם                                            | סוג        | למה זה משמש                            |
| --------------------------------------------- | ---------- | -------------------------------------- |
| `AWS_REGION`                                  | Var/Secret | אזור AWS (למשל `eu-central-1`)         |
| `EKS_CLUSTER_NAME`                            | Var/Secret | שם הקלאסטר (למשל `fm-eks`)             |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | Secret     | אם לא עובדים עם OIDC                   |
| `KUBECONFIG_B64`                              | Secret     | אופציונלי – אם בחרתם CD דרך kubeconfig |

> מומלץ OIDC (Role ב-AWS עם trust ל-GitHub) במקום מפתחות סטטיים.

---

## נקודות פרונט-אנד

* RTL מובנה; אזורי אנגלית מוגדרים `.ltr`.
* וידאו/טיפ/ציטוט כוללים **חיצים עגולים** (RTL-aware).
* "יש לכם רעיון?" — טופס שמתווסף ל-`app/data/ideas.json`.

---

## בדיקות מהירות

```bash
curl http://<LB-DNS>/healthz
kubectl -n prod logs deploy/fm-app
kubectl -n prod get deploy,svc,ingress
```

---

## תקלות נפוצות

* **ImagePullBackOff** — בדקו שה-image קיים ושם הנתיב נכון (`ghcr.io/<owner>/<repo>:<tag>`). אם GHCR פרטי – הגדירו `imagePullSecret`.
* **אין EXTERNAL-IP** — ודאו `type: LoadBalancer`, תתי-רשת ציבוריים, והרשאות ב-AWS.
* **"You must be logged in to the server"** — עדכנו kubeconfig/הרשאות (או OIDC).
* **404 ל-quotes/tips** — ודאו שקבצי ה-JSON קיימים תחת `app/data`.

---

## ניקוי ועלויות

EKS/NAT/LoadBalancer עולים כסף. בסיום:

```bash
cd infra
terraform destroy -var-file=dev.tfvars -auto-approve
```

### ניקוי Images ישנים ב-GHCR

צרו Workflow:

```yaml
# .github/workflows/ghcr-cleanup.yml
name: Cleanup GHCR
on:
  workflow_dispatch:
  schedule:
    - cron: "0 3 * * 0"

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
          package-name: "${{ github.repository }}"   # בד"כ <owner>/<repo>
          min-versions-to-keep: 15
          delete-only-untagged-versions: true
```

### ניקוי מקומי (Docker)

```bash
docker image prune -a
docker system prune -a --volumes
```

