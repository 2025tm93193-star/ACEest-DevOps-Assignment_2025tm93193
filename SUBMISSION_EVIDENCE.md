# ACEest DevOps Assignment 1 — submission and screenshot checklist

Only mark a checkbox after the associated command, web page, or pipeline truly succeeded. Do not manufacture screenshots.

| # | Evidence to capture | Where/how to capture | Done |
|---|---|---|---|
| 01 | VM OS, Python, Git and Docker environment | terminal `cat /etc/os-release`, `python3 --version`, etc. | ☐ |
| 02 | Source project structure and original 10 versions | terminal `ls -la` and `find instructor_versions ...` | ☐ |
| 03 | Running Flask browser dashboard with a client | VM browser at `http://127.0.0.1:5000` | ☐ |
| 04 | Unit tests pass | terminal `python -m pytest -v` | ☐ |
| 05 | Health endpoint works | terminal `curl -i http://127.0.0.1:5000/health` | ☐ |
| 06 | Public GitHub repository files | GitHub repo page with `.github/workflows` | ☐ |
| 07 | Meaningful Git commit history | terminal `git log --oneline --graph -5` | ☐ |
| 08 | Docker image builds | terminal `docker build` and `docker images` | ☐ |
| 09 | Tests pass inside Docker | terminal `docker run --rm --entrypoint python ... -m pytest -q` | ☐ |
| 10 | GitHub Actions workflow succeeds | Actions tab, green `verify` job | ☐ |
| 11 | GitHub Actions individual steps | expanded tests and Docker steps | ☐ |
| 12 | Jenkins SCM/job configuration | Jenkins Pipeline definition and GitHub URL (redact secrets) | ☐ |
| 13 | Jenkins BUILD succeeds | Jenkins Stage View or job summary | ☐ |
| 14 | Jenkins console build/test log | Jenkins Console Output | ☐ |

## Submission metadata (fill in after execution)

- GitHub URL: `https://github.com/YOUR_USERNAME/ACEest-DevOps-Assignment`
- Git branch: `main`
- Local Pytest result: `NOT YET VERIFIED ON VM`
- Docker build result: `NOT YET VERIFIED ON VM`
- GitHub Actions run URL: `NOT YET VERIFIED`
- Jenkins job URL/build #: `NOT YET VERIFIED`

## Final checks

- [ ] Public repository contains source code, `requirements.txt`, tests, `Dockerfile`, and `Jenkinsfile`.
- [ ] `.github/workflows/main.yml` is committed, and its workflow run passed.
- [ ] Real screenshots prove local tests, Docker build/tests, and Jenkins BUILD when available.
- [ ] No passwords, PATs, private keys, student identifiers, or local database files were committed.
- [ ] README describes what was adapted from the instructor code and what is missing.
- [ ] Submission contains the public GitHub URL and any evidence requested by the instructor.
