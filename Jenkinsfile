pipeline {
  agent any
  options { timestamps() }
  stages {
    stage('Checkout') {
      steps { checkout scm }
    }
    stage('Secret Scan - Gitleaks') {
      steps {
        sh '''
          docker run --rm --volumes-from jenkins -w "$WORKSPACE" \
            ghcr.io/gitleaks/gitleaks:latest \
            detect --source . --no-git --verbose --redact
        '''
      }
    }
    stage('SAST - Bandit') {
      steps {
        catchError(buildResult: 'SUCCESS', stageResult: 'UNSTABLE') {
          sh '''
            docker run --rm --volumes-from jenkins -w "$WORKSPACE" \
              python:3.12-slim sh -c \
              "pip install -q bandit && bandit -r backend frontend -ll"
          '''
        }
      }
    }
    stage('SCA - pip-audit') {
      steps {
        catchError(buildResult: 'SUCCESS', stageResult: 'UNSTABLE') {
          sh '''
            docker run --rm --volumes-from jenkins -w "$WORKSPACE" \
              python:3.12-slim sh -c \
              "pip install -q pip-audit && pip-audit -r backend/requirements.txt && pip-audit -r frontend/requirements.txt"
          '''
        }
      }
    }
  }
}