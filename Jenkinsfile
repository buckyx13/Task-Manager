pipeline {
  agent any
  stages {
    stage('Checkout') {
      steps { echo 'Code pulled from Git' }
    }
    stage('Verify') {
      steps { sh 'ls -la && python3 --version || true' }
    }
  }
}