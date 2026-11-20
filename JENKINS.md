# AgriSmart AI — Jenkins CI/CD Guide

## Pipeline overview

```
Push to GitHub main
       │
       ▼
  1. Checkout
  2. Environment Setup
  3. Build Docker Images  (API + Test — parallel)
  4. Unit Tests           (pytest -m unit)
  5. Integration Tests    (pytest -m integration)
  6. E2E Tests            (pytest -m e2e + Playwright)
  7. Coverage Gate        (fails if < 70%)
  8. Security Scan        (Bandit — flags HIGH findings)
  9. Push to Registry     (Docker Hub — main branch only)
 10. Deploy               (docker-compose up)
```

---

## First-time Jenkins setup

### 1. Start Jenkins via Docker Compose

```bash
docker-compose up -d jenkins
```

Open http://localhost:8080

### 2. Get the initial admin password

```bash
docker exec agrismart_jenkins \
  cat /var/jenkins_home/secrets/initialAdminPassword
```

### 3. Install recommended plugins, then also install:
- **Docker Pipeline**
- **GitHub Integration**
- **JUnit**
- **HTML Publisher** (for coverage reports)
- **Credentials Binding**

### 4. Add Docker Hub credentials

Jenkins → Manage Jenkins → Credentials → Add:
- Kind: Username with password
- ID: `dockerhub-creds`
- Username: your Docker Hub username
- Password: your Docker Hub password / token

### 5. Create a Pipeline job

1. New Item → Pipeline
2. GitHub Project → `https://github.com/aayushspundir2007-dot/Agri-ai`
3. Build Triggers → GitHub hook trigger for GITScm polling
4. Pipeline → Pipeline script from SCM → Git
5. Script Path: `Jenkinsfile`

### 6. Set up GitHub webhook

GitHub repo → Settings → Webhooks → Add webhook:
- Payload URL: `http://your-jenkins-server:8080/github-webhook/`
- Content type: `application/json`
- Events: Just the push event

---

## Update `Jenkinsfile` for your registry

Edit `Jenkinsfile` line:
```groovy
REGISTRY = "your-dockerhub-username"  // change this
```

---

## Running the pipeline manually

Jenkins → Your job → Build Now

---

## Viewing reports in Jenkins

After a build:
- **Test results**: Build → Test Results (JUnit)
- **Coverage**: Build → Coverage Report (HTML Publisher)
- **Console log**: Build → Console Output
- **Artifacts**: Build → Artifacts (`reports/`)

---

## Pipeline stages explained

| Stage | What it does | Fails on |
|---|---|---|
| Checkout | Clones GitHub repo | Unreachable repo |
| Environment Setup | Checks Docker, creates .env | Docker not installed |
| Build Images | docker build (parallel) | Dockerfile errors |
| Unit Tests | pytest -m unit inside Docker | Any test failure |
| Integration Tests | pytest -m integration with live API | API startup failure |
| E2E Tests | pytest -m e2e with Playwright | Browser/page errors |
| Coverage Gate | Parses coverage.xml | Coverage < 70% |
| Security Scan | Bandit static analysis | HIGH severity (unstable) |
| Push to Registry | docker push | Bad credentials |
| Deploy | docker-compose up | Health check failure |
