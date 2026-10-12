# ACEest DevOps Assignment — Prayogshala VM step-by-step implementation

This guide is for a Linux-based Prayogshala lab VM. **Check your actual OS and permission level before installing system software.** Commands are meant to run one stage at a time; capture results in `SUBMISSION_EVIDENCE.md`.

## Stage 0 — Prepare your lab VM

Log in to your VM and open **Terminal**. Run:

```bash
cat /etc/os-release | head -n 6
whoami
id
pwd
python3 --version || true
python3 -m pip --version || true
git --version || true
docker --version || true
docker info || true
java -version || true
jenkins --version || true
systemctl is-active jenkins || true
df -h .
```

**Expected:** identify distro, Python 3, Git, Docker daemon state, Jenkins service state. A `command not found` or Docker daemon error means it needs installation/configuration. It is normal for Jenkins to be absent initially.

On Ubuntu/Debian, **only if permitted to use sudo**, install missing Python/Git prerequisites:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git curl
```

If `sudo` is unavailable or packages are restricted by Prayogshala, request tools from your course administrator; do not attempt to bypass VM restrictions.

**Screenshot 01:** terminal with `python3 --version`, `git --version`, `docker --version` (if installed), OS and username.

## Stage 1 — Transfer and inspect the project

1. Download `ACEest-DevOps-Complete.zip` from the assistant on your own computer.
2. Upload it through the Prayogshala file-transfer interface (or use approved `scp` to your VM).
3. In the directory containing the ZIP:

```bash
unzip 'ACEest-DevOps-Complete.zip'
cd ACEest-DevOps-Complete
ls -la
find instructor_versions -maxdepth 1 -name '*.py' -type f | sort
find .github -type f
```

**Expected:** 10 original scripts plus `aceest/`, `tests/`, `Dockerfile`, `Jenkinsfile`, `README.md` and `.github/workflows/main.yml`.

**Screenshot 02:** directory listing showing main project files and original versions.

## Stage 2 — Install Python dependencies, start application and test

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m compileall -q app.py aceest tests instructor_versions
ruff check app.py aceest tests
python -m pytest -v
```

**Expected:** no syntax or Ruff errors; Pytest finishes with all tests passing. If installation fails, check VM internet access and the error message. If `venv` fails, install `python3-venv` if allowed.

Now start the web application:

```bash
python app.py
```

Open `http://127.0.0.1:5000` in a browser **on the VM**. If your browser is outside the VM, use the environment's approved port-forwarding method; avoid exposing the unauthenticated app on the internet.

In a second terminal:

```bash
curl -i http://127.0.0.1:5000/health
```

Use the browser to create a client, assign a program, record adherence and record a workout. Test the API with `curl` commands in the README. Stop the server using `Ctrl+C`.

**Screenshot 03:** browser showing ACEest web dashboard with a created client.

**Screenshot 04:** terminal showing passing `python -m pytest -v`.

**Screenshot 05:** successful `/health` HTTP response.

## Stage 3 — Set up meaningful Git history

Go to https://github.com/new and create a **public, empty repository** `ACEest-DevOps-Assignment`. Do **not** tick “Add README” when creating the repository.

From the project root:

```bash
git init
git config user.name "YOUR NAME"
git config user.email "YOUR GITHUB EMAIL"
git add instructor_versions/
git commit -m "chore: archive instructor ACEest versions"
git add app.py aceest/ requirements.txt .gitignore pytest.ini ruff.toml
git commit -m "feat: adapt ACEest features to Flask and SQLite"
git add tests/
git commit -m "test: cover Flask API and domain logic with pytest"
git add Dockerfile .dockerignore
git commit -m "build: containerize Flask application"
git add .github/workflows/main.yml Jenkinsfile README.md IMPLEMENTATION_GUIDE.md SUBMISSION_EVIDENCE.md
git commit -m "ci: add GitHub Actions and Jenkins pipelines"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/ACEest-DevOps-Assignment.git
git push -u origin main
git log --oneline --graph -5
git status
```

Replace all placeholders with your real identity and repository URL. GitHub may ask for sign-in, token, or SSH key; do not use your GitHub account password as a Git password.

**Expected:** remote GitHub page has all files (including hidden `.github/`), there are several meaningful commits, and `git status` says the working tree is clean.

**Screenshot 06:** GitHub repository file listing.

**Screenshot 07:** `git log --oneline` showing multiple commits.

## Stage 4 — Build and test Docker

First verify the daemon:

```bash
docker --version
docker info
```

If Docker is missing, install using an administrator-approved process and the distribution-specific official installation guide: https://docs.docker.com/engine/install/ . For an Ubuntu/Debian **training** VM with supported package repositories and sudo access, `sudo apt install docker.io` may be an available distro package, followed by `sudo systemctl enable --now docker`; use your institution's instructions if they differ. Do not mix conflicting Docker package sources. If Docker daemon access is denied, obtain administrator assistance.

```bash
docker build -t aceest-fitness:local .
docker images | grep aceest
# Run the app (leave this terminal open)
docker run --rm -p 127.0.0.1:5000:5000 --name aceest-app aceest-fitness:local
```

In a second terminal:

```bash
curl -i http://127.0.0.1:5000/health
docker run --rm --entrypoint python aceest-fitness:local -m pytest -q
```

Stop the running container using `Ctrl+C`.

**Screenshot 08:** Docker build success and `docker images` listing.

**Screenshot 09:** `docker run --rm --entrypoint python ... -m pytest -q` showing passed tests.

## Stage 5 — Verify GitHub Actions

1. Open the public repo on GitHub.
2. Go to **Actions** → **ACEest CI - lint, test and Docker** → latest run.
3. Ensure the `verify` job passes every stage, including the **Build Docker image** and **Run tests inside Docker container** steps.
4. If no run has started yet, push a small real documentation edit using Git. Don't create fake output.
5. If a run fails, click its failing step, copy the error, fix it locally, commit, and push again.

**Screenshot 10:** Actions run with green success check and job summary.

**Screenshot 11:** expanded steps showing Pytest and Docker container tests succeeded.

## Stage 6 — Install/configure Jenkins BUILD

First check if Jenkins is already provided by Prayogshala. If so, prefer that managed installation. You only need a Jenkins account with permission to create jobs and a Linux build agent with Git, Python, and Docker access.

If you are authorized to install Jenkins yourself on **Ubuntu/Debian**:

```bash
sudo apt update
sudo apt install -y fontconfig openjdk-21-jre wget
java -version
sudo install -d -m 0755 /etc/apt/keyrings
sudo wget -O /etc/apt/keyrings/jenkins-keyring.asc \
  https://pkg.jenkins.io/debian-stable/jenkins.io-2026.key
echo 'deb [signed-by=/etc/apt/keyrings/jenkins-keyring.asc] https://pkg.jenkins.io/debian-stable binary/' \
  | sudo tee /etc/apt/sources.list.d/jenkins.list >/dev/null
sudo apt update
sudo apt install -y jenkins
sudo systemctl enable --now jenkins
systemctl is-active jenkins
```

These commands follow the official Jenkins Debian/Ubuntu LTS installation pattern as of October 2026. Confirm current instructions at https://www.jenkins.io/doc/book/installing/linux/ if repository keys or package requirements change. A web UI is normally reachable at `http://127.0.0.1:8080` **from the VM** if networking permits. On first start, follow the unlock/setup screen, normally using `/var/lib/jenkins/secrets/initialAdminPassword` (requires VM admin rights), install suggested plugins, and create your admin account. Do not publish Jenkins to the internet without appropriate authentication and network controls.

### Create the Jenkins Pipeline job

1. Jenkins → **New Item** → enter `ACEest-BUILD` → **Pipeline** → OK.
2. Under **Pipeline**, set **Definition** to `Pipeline script from SCM`.
3. SCM: **Git**. Repository URL: `https://github.com/YOUR_USERNAME/ACEest-DevOps-Assignment.git`.
4. Branch Specifier: `*/main`; Script Path: `Jenkinsfile`.
5. Save → **Build Now**.
6. Open **Console Output** and confirm all stages succeed.

If `docker info` fails for Jenkins, the Jenkins build agent does not have daemon access. On a trusted lab VM, the administrator may elect to give the Jenkins agent access to Docker; membership in the `docker` group grants root-equivalent privileges, so only do this with authorization. Jenkins needs Python `venv` and outbound access for `pip install` and Docker image pulls.

**Screenshot 12:** Jenkins job configuration showing GitHub SCM, branch, and `Jenkinsfile` (hide credentials and tokens).

**Screenshot 13:** green Jenkins successful build / Stage View.

**Screenshot 14:** Console Output confirming checkout, tests, Docker build, and container tests passed.

## Stage 7 — Optional CI trigger demonstration

GitHub Actions already runs automatically for pushes and pull requests. For Jenkins, use the course-provided approved polling/webhook process if requested. A public GitHub webhook cannot reach a local-only Jenkins server unless there is a secure reachable endpoint. A manual **Build Now** is sufficient to demonstrate a working Jenkins BUILD pipeline if automatic Jenkins triggering is not explicitly required.

## Stage 8 — Submit

Check your public repository and screenshot evidence. Add *genuine* evidence in a private document or instructor-approved submission portal, without exposing API tokens, Jenkins unlock passwords, or student credentials. Share the GitHub URL.

If your VM cannot run Docker/Jenkins due to resource or sudo restrictions, you can still run **GitHub Actions on GitHub-hosted runners** from the public repository; document the missing Jenkins environment truthfully and ask the lab admin for a Jenkins-capable machine. Do not represent GitHub Actions as proof of Jenkins execution.

## Quick troubleshooting

| Symptom | Likely reason and fix |
|---|---|
| `python3: command not found` | Python isn't installed; request VM install or use supported Python binary |
| `No module named venv` | Install the matching `python3-venv` OS package, if authorized |
| `No module named flask` | Activate `.venv`, then `python -m pip install -r requirements.txt` |
| Pytest cannot import `aceest` | Run from project root; use `python -m pytest`, not `pytest` from another directory |
| `Address already in use` on port 5000 | Stop an existing Flask/Docker process or remap the host port |
| Docker permission denied | Ask admin for approved daemon access; docker group is root-equivalent |
| Docker daemon not running | Check `docker info`, `systemctl status docker`, and VM service policy |
| Actions doesn't appear | Workflow must be committed at `.github/workflows/main.yml` on GitHub |
| Jenkins has no Git step | Install/enable official Git and Pipeline plugins on the Jenkins server |
| Jenkins has no Docker | Use an approved Docker-enabled Jenkins Linux agent |
| Jenkins unreachable on 8080 | Check Jenkins service, network/port access or SSH tunnel setup |
