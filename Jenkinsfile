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
    // stage('SAST - Bandit') {
    //   steps {
    //     catchError(buildResult: 'SUCCESS', stageResult: 'UNSTABLE') {
    //       sh '''
    //         docker run --rm --volumes-from jenkins -w "$WORKSPACE" \
    //           python:3.12-slim sh -c \
    //           "pip install -q bandit && bandit -r backend frontend -ll"
    //       '''
    //     }
    //   }
    // }
    // stage('SCA - pip-audit') {
    //   steps {
    //     catchError(buildResult: 'SUCCESS', stageResult: 'UNSTABLE') {
    //       sh '''
    //         docker run --rm --volumes-from jenkins -w "$WORKSPACE" \
    //           python:3.12-slim sh -c \
    //           "pip install -q pip-audit && pip-audit -r backend/requirements.txt && pip-audit -r frontend/requirements.txt"
    //       '''
    //     }
    //   }
    // }
    stage('SAST - Bandit') {
      steps {
        sh '''
          docker run --rm --volumes-from jenkins -w "$WORKSPACE" \
            python:3.12-slim sh -c \
            "pip install -q bandit && bandit -r backend frontend -ll"
        '''
      }
    }
    stage('SCA - pip-audit') {
      steps {
        sh '''
          docker run --rm --volumes-from jenkins -w "$WORKSPACE" \
            python:3.12-slim sh -c \
            "pip install -q pip-audit && pip-audit -r backend/requirements.txt -r frontend/requirements.txt"
        '''
      }
    }
    stage('Dockerfile Lint - Hadolint') {
      steps {
        sh '''
          docker run --rm -i hadolint/hadolint < backend/Dockerfile
          docker run --rm -i hadolint/hadolint < frontend/Dockerfile
        '''
      }
    }
    stage('Build Images') {
      steps {
        sh '''
          docker build -t task-backend:${BUILD_NUMBER} backend
          docker build -t task-frontend:${BUILD_NUMBER} frontend
        '''
      }
    }
    stage('Image Scan - Trivy') {
      steps {
        sh '''
          for img in task-backend task-frontend; do
            docker run --rm \
              -v /var/run/docker.sock:/var/run/docker.sock \
              -v trivy-cache:/root/.cache \
              aquasec/trivy:latest image \
              --severity HIGH,CRITICAL --ignore-unfixed --exit-code 1 \
              $img:${BUILD_NUMBER}
          done
        '''
      }
    }
  }
}