pipeline {
    agent any

    options { timestamps() }

    stages {
        stage('Checkout from GitHub') {
            steps { checkout scm }
        }
        stage('Verify build prerequisites') {
            steps {
                sh 'python3 --version'
                sh 'git --version'
                sh 'docker info >/dev/null'
            }
        }
        stage('Python build and lint') {
            steps {
                sh 'python3 -m venv .venv'
                sh '. .venv/bin/activate && python -m pip install -r requirements.txt'
                sh '. .venv/bin/activate && python -m compileall -q app.py aceest tests instructor_versions'
                sh '. .venv/bin/activate && ruff check app.py aceest tests'
            }
        }
        stage('Pytest') {
            steps { sh '. .venv/bin/activate && python -m pytest -q' }
        }
        stage('Build Docker image') {
            steps { sh 'docker build -t aceest-fitness:jenkins .' }
        }
        stage('Test Docker image') {
            steps {
                sh 'docker run --rm --entrypoint python aceest-fitness:jenkins -m pytest -q'
            }
        }
    }
    post {
        success { echo 'ACEest BUILD and tests PASSED' }
        failure { echo 'ACEest BUILD FAILED: inspect Console Output' }
    }
}
