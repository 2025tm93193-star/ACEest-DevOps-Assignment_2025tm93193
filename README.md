# ACEest Fitness & Gym — Introduction to DevOps Assignment 1

A classroom demonstration of **continuous integration and build automation** using **Flask, SQLite, Pytest, Docker, Git, GitHub Actions and Jenkins**, adapted from the ACEest application versions supplied by the instructor.

> **Source attribution and scope:** All 10 unmodified original Tkinter scripts from the uploaded ZIP are in [`instructor_versions/`](instructor_versions/). The application we run and test here is a **new Flask adaptation** using the fitness-program templates and client/workout/progress/metric concepts from `Aceestver-3.2.4.py`. This is **not an unchanged execution** of the Tkinter GUI. The instructor scripts are archived for comparison. The application's original role-based login is deliberately **not** reproduced because it uses an insecure hardcoded `admin/admin` account. The new demo API has **no authentication**, so use it **only in a local/trusted lab**, never publicly expose member data.

## Key application features

- Web dashboard at `/` and health endpoint `/health`.
- Client registration, listing, details and profile/membership updates.
- Instructor-provided Fat Loss / Muscle Gain / Beginner program templates.
- Weekly fitness adherence, workout and exercise logs, body metrics.
- SQLite persistence and downloadable PDF report for a client.
- Automated API tests with an isolated temporary SQLite database.
- Python syntax checks, Ruff linting, Pytest, Docker image build, containerized tests in GitHub Actions and Jenkins.

*Not included in the new Flask UI:* the original Tkinter screens, matplotlib graphical charts, authentication/roles, real billing/payment handling, and any real AI recommendation engine. The browser UI exposes a subset of API capabilities; the rest are testable using `curl` and Pytest.

## Project layout

```text
ACEest-DevOps-Complete/
├── app.py                         # Flask entry point
├── aceest/
│   ├── __init__.py                # application factory
│   ├── database.py                # SQLite schema and connection lifecycle
│   ├── domain.py                  # original instructor program templates
│   ├── routes.py                  # Flask APIs, validation, PDF export
│   └── templates/index.html      # simple web demo dashboard
├── instructor_versions/          # all 10 instructor-provided original .py files
├── tests/test_app.py              # isolated unit/API tests
├── requirements.txt              # app, test, build dependencies
├── Dockerfile
├── .dockerignore
├── .gitignore
├── pytest.ini
├── ruff.toml
├── .github/workflows/main.yml     # CI on push and pull request
├── Jenkinsfile                    # Jenkins BUILD pipeline
├── IMPLEMENTATION_GUIDE.md        # commands for your Prayogshala VM
└── SUBMISSION_EVIDENCE.md         # required evidence checklist
```

## 1. Requirements

- Linux VM with `python3`, `python3-venv`, `git`, internet access to install packages.
- Docker Engine with a working daemon if performing container stages.
- GitHub account and public repository.
- Jenkins server/agent with Linux shell, Git, Python, and permission to access the Docker daemon for the separate Jenkins BUILD stage.

Python 3.12 is used by the pipeline and Docker image. A compatible local Python 3.12+ may work as well.

For a complete system checklist and troubleshooting, see **[IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md)**.

## 2. Install and run locally (Linux / Prayogshala)

```bash
cd ACEest-DevOps-Complete
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000` **in the VM's browser**. On a remote VM, SSH port forwarding may be required; don't assume the VM's port is externally accessible.

Open another terminal in the project directory:

```bash
curl -i http://127.0.0.1:5000/health
```

Expected JSON includes `"status":"ok"`. The SQLite database is stored in `instance/aceest.sqlite3` by default and ignored by Git; override with `ACEEST_DB_PATH` if needed.

## 3. Run syntax, lint, and tests

With your virtual environment activated:

```bash
python -m compileall -q app.py aceest tests instructor_versions
ruff check app.py aceest tests
python -m pytest -v
```

The tests cover health, program templates, create/update/list clients, validation errors, duplicate handling, workout/exercise logs, adherence, body metrics and PDF export. Pytest runs against fresh temporary test databases. Do not run the instructor's Tkinter windows in headless GitHub Actions/Docker.

## 4. Docker: build, run, test

```bash
docker info
docker build -t aceest-fitness:local .
docker run --rm -p 127.0.0.1:5000:5000 --name aceest-app aceest-fitness:local
```

In another terminal:

```bash
curl -i http://127.0.0.1:5000/health
docker run --rm --entrypoint python aceest-fitness:local -m pytest -q
```

Stop the running app using `Ctrl+C`. For persistence across container recreations, make a host directory and mount it:

```bash
mkdir -p instance
docker run --rm -p 127.0.0.1:5000:5000 \
  -v "$PWD/instance:/app/instance" aceest-fitness:local
```

**Note:** The image runs as a non-root `aceest` user. The host-mounted `instance` directory must be writable by that user (the image uses a dedicated UID). For an uncomplicated classroom demo, first run without the bind mount; Docker named volumes or managed directory permissions are a separate exercise. Data without a volume is ephemeral when a container is removed.

## 5. API examples

```bash
# Create a client
curl -i -X POST http://127.0.0.1:5000/api/clients \
  -H 'Content-Type: application/json' \
  -d '{"name":"Asha","age":29,"weight":64.5,"membership_status":"Active"}'

# List clients
curl http://127.0.0.1:5000/api/clients

# Generate template for client #1 (change ID if needed)
curl -i -X POST http://127.0.0.1:5000/api/clients/1/program \
  -H 'Content-Type: application/json' \
  -d '{"goal":"Muscle Gain"}'

# Record weekly progress
curl -i -X POST http://127.0.0.1:5000/api/clients/1/progress \
  -H 'Content-Type: application/json' \
  -d '{"week":"2026-W41","adherence":85}'

# Download client report
curl -o client-report.pdf http://127.0.0.1:5000/api/clients/1/report.pdf
```

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Demo dashboard |
| `/health` | GET | Health status |
| `/api/programs` | GET | Source-defined program templates |
| `/api/clients` | GET, POST | List/create clients |
| `/api/clients/<id>` | GET, PATCH | Read/update a client |
| `/api/clients/<id>/program` | POST | Assign template program |
| `/api/clients/<id>/progress` | GET, POST | Read/save weekly adherence |
| `/api/clients/<id>/workouts` | GET, POST | Read/save workouts and exercises |
| `/api/clients/<id>/metrics` | GET, POST | Read/save body metrics |
| `/api/clients/<id>/report.pdf` | GET | Download PDF report |

## 6. Git and GitHub

Create an **empty public** GitHub repository named `ACEest-DevOps-Assignment` (do not initialize GitHub's README). In the project root, run:

```bash
git init
git add instructor_versions/
git commit -m "chore: archive instructor ACEest versions"
git add app.py aceest/ requirements.txt .gitignore pytest.ini ruff.toml
git commit -m "feat: adapt ACEest features to Flask and SQLite"
git add tests/
git commit -m "test: cover Flask API and domain logic with pytest"
git add Dockerfile .dockerignore
git commit -m "build: containerize Flask application"
git add .github/workflows/main.yml Jenkinsfile README.md IMPLEMENTATION_GUIDE.md SUBMISSION_EVIDENCE.md
git commit -m "ci: add GitHub Actions and Jenkins build pipelines"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/ACEest-DevOps-Assignment.git
git push -u origin main
```

Replace `YOUR_USERNAME`. When asked for credentials, authenticate using GitHub's supported login flow/token or an SSH key; an account password is not a Git HTTPS password. Never commit tokens. If your repo exists and `origin` has already been set, check `git remote -v` and use `git remote set-url origin <repository-url>`.

## 7. GitHub Actions CI

Workflow: [`.github/workflows/main.yml`](.github/workflows/main.yml).

On **every push and pull request** the `verify` job:

1. checks out source code;
2. sets up Python 3.12 and installs requirements;
3. compiles application, tests, and original source scripts;
4. runs Ruff linting on active application and tests;
5. runs Pytest;
6. builds a Docker image;
7. runs Pytest **inside the built Docker image**.

After the push, open **GitHub → your repository → Actions → ACEest CI → latest workflow** and confirm all steps are green. A workflow file existing in a repository is **not** proof of a successful run.

## 8. Jenkins BUILD environment

A Linux Jenkins agent needs Git, Python 3 / `venv`, and access to a running Docker daemon. The [`Jenkinsfile`](Jenkinsfile) has checkout, prerequisites, Python compile/lint, Pytest, Docker build, and Docker tests.

Recommended job configuration:

1. Jenkins Dashboard → **New Item** → `ACEest-BUILD` → **Pipeline**.
2. **Pipeline → Definition: Pipeline script from SCM**.
3. SCM: **Git**; Repository URL: `https://github.com/YOUR_USERNAME/ACEest-DevOps-Assignment.git`.
4. Branch: `*/main`; Script Path: `Jenkinsfile`.
5. Save → **Build Now** → check **Stage View / Console Output**.
6. Optional: configure Jenkins to poll SCM, or a GitHub webhook if Jenkins is securely reachable by GitHub. Do not publicly expose an unsecured Jenkins instance.

If Jenkins Docker commands fail with `permission denied` on `/var/run/docker.sock`, ask the VM administrator for an approved Docker-enabled agent. Membership in the `docker` group gives root-level access and should only be granted on a trusted training VM.

## 9. Deliverables and screenshots

See [`SUBMISSION_EVIDENCE.md`](SUBMISSION_EVIDENCE.md). Capture *genuine* screenshots showing tests and both CI systems. Submit your public GitHub link as requested by your instructor.

## 10. Constraints and known limitations

- This is a **teaching/lab demo**, not production software. No authentication, authorization, TLS termination, secrets management, migrations, database backups, automated CD deployment, or complete test coverage of a browser's JavaScript UI.
- Source templates are randomly selected; the original scripts call this “AI-style” generation, but no AI model is used.
- The Tkinter UI and matplotlib chart rendering remain only in archived original files; headless CI tests the Flask adaptation.
- The Dockerfile includes test tools to satisfy the assignment's *test-inside-the-container* requirement, not to minimize a production image.
- Jenkins and GitHub Actions are separate CI systems; one is not required to call the other.
- Dependencies are bounded ranges, not a fully locked supply chain. For production work, use a dependency lockfile and stronger security practices.
