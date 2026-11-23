pipeline {
  agent any
  options {
    timestamps()
    disableConcurrentBuilds(abortPrevious: true)
  }
  triggers {
    cron('H 20 * * *')
    pollSCM('H/5 * * * *')
  }
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
    stage('IaC Scan - Checkov') {
      steps {
        sh '''
          docker run --rm --volumes-from jenkins -w "$WORKSPACE" \
            bridgecrew/checkov:latest \
            -f backend/Dockerfile -f frontend/Dockerfile \
            --framework dockerfile --compact --quiet
        '''
      }
    }
    stage('Build Images') {
      steps {
        sh '''
          docker build --pull -t task-backend:${BUILD_NUMBER} backend
          docker build --pull -t task-frontend:${BUILD_NUMBER} frontend
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
    stage('Deploy Test Env') {
      steps {
        withCredentials([
          string(credentialsId: 'db-user', variable: 'DB_USER'),
          string(credentialsId: 'db-password', variable: 'DB_PASSWORD'),
          string(credentialsId: 'db-name', variable: 'DB_NAME')
        ]) {
          sh '''
            NET=net-$BUILD_NUMBER
            docker network create $NET

            export POSTGRES_USER="$DB_USER" POSTGRES_PASSWORD="$DB_PASSWORD" POSTGRES_DB="$DB_NAME"
            docker run -d --name db-$BUILD_NUMBER --network $NET \
              -e POSTGRES_USER -e POSTGRES_PASSWORD -e POSTGRES_DB postgres:16

            for i in $(seq 1 30); do
              docker exec db-$BUILD_NUMBER pg_isready -h 127.0.0.1 -U "$DB_USER" && break
              sleep 2
            done
            docker exec -i db-$BUILD_NUMBER psql -U "$DB_USER" -d "$DB_NAME" < database/init.sql

            docker run -d --name backend-$BUILD_NUMBER --network $NET \
              -e DB_HOST=db-$BUILD_NUMBER -e DB_NAME -e DB_USER -e DB_PASSWORD \
              task-backend:$BUILD_NUMBER
            docker run -d --name frontend-$BUILD_NUMBER --network $NET \
              -e BACKEND_URL=http://backend-$BUILD_NUMBER:5000 \
              task-frontend:$BUILD_NUMBER

            for i in $(seq 1 30); do
              docker run --rm --network $NET curlimages/curl -sf \
                http://backend-$BUILD_NUMBER:5000/health >/dev/null && \
              docker run --rm --network $NET curlimages/curl -sf \
                http://frontend-$BUILD_NUMBER:8000/ >/dev/null && exit 0
              sleep 2
            done
            echo "App did not become ready"
            docker logs backend-$BUILD_NUMBER
            docker logs frontend-$BUILD_NUMBER
            exit 1
          '''
        }
      }
    }
    stage('DAST - OWASP ZAP') {
      steps {
        script {
          sh '''
            docker volume create zap-wrk-$BUILD_NUMBER
            docker run --rm -v zap-wrk-$BUILD_NUMBER:/zap/wrk busybox chmod 777 /zap/wrk
          '''
          def rc = sh(returnStatus: true, script: '''
            docker run --name zap-$BUILD_NUMBER \
              --network net-$BUILD_NUMBER \
              -v zap-wrk-$BUILD_NUMBER:/zap/wrk \
              ghcr.io/zaproxy/zaproxy:stable zap-baseline.py \
              -t http://frontend-$BUILD_NUMBER:8000 \
              -r zap-report.html
          ''')
          sh 'docker cp zap-$BUILD_NUMBER:/zap/wrk/zap-report.html . || true'
          if (rc == 1 || rc == 2) {
            unstable("ZAP reported findings (exit code ${rc})")
          } else if (rc != 0) {
            error("ZAP failed to run (exit code ${rc})")
          }
        }
      }
    }
    stage('Push to Docker Hub') {
      when { not { triggeredBy 'TimerTrigger' } }
      steps {
        withCredentials([usernamePassword(credentialsId: 'dockerhub-creds',
                         usernameVariable: 'DH_USER', passwordVariable: 'DH_TOKEN')]) {
          sh '''
            echo "$DH_TOKEN" | docker login -u "$DH_USER" --password-stdin
            for svc in backend frontend; do
              docker tag task-$svc:$BUILD_NUMBER $DH_USER/task-$svc:$BUILD_NUMBER
              docker push $DH_USER/task-$svc:$BUILD_NUMBER
            done
            docker logout
          '''
        }
      }
    }
    stage('Approval') {
      when { not { triggeredBy 'TimerTrigger' } }
      steps {
        timeout(time: 30, unit: 'MINUTES') {
          input message: "Deploy build ${BUILD_NUMBER} to production?", ok: 'Deploy'
        }
      }
    }
    stage('Deploy to Production') {
      when { not { triggeredBy 'TimerTrigger' } }
      steps {
        withCredentials([
          usernamePassword(credentialsId: 'dockerhub-creds',
                           usernameVariable: 'DH_USER', passwordVariable: 'DH_TOKEN'),
          string(credentialsId: 'prod-db-user', variable: 'DB_USER'),
          string(credentialsId: 'prod-db-password', variable: 'DB_PASSWORD'),
          string(credentialsId: 'prod-db-name', variable: 'DB_NAME')
        ]) {
          sh '''
            docker network inspect prod-net >/dev/null 2>&1 || docker network create prod-net

            # Create the database only once; data lives in a named volume
            if ! docker ps -a --format '{{.Names}}' | grep -qx prod-db; then
              export POSTGRES_USER="$DB_USER" POSTGRES_PASSWORD="$DB_PASSWORD" POSTGRES_DB="$DB_NAME"
              docker run -d --name prod-db --network prod-net --restart unless-stopped \
                -v prod-pgdata:/var/lib/postgresql/data \
                -e POSTGRES_USER -e POSTGRES_PASSWORD -e POSTGRES_DB postgres:16
              for i in $(seq 1 30); do
                docker exec prod-db pg_isready -h 127.0.0.1 -U "$DB_USER" && break
                sleep 2
              done
              docker exec -i prod-db psql -U "$DB_USER" -d "$DB_NAME" < database/init.sql
            fi

            # Pull the exact versioned images from the registry
            echo "$DH_TOKEN" | docker login -u "$DH_USER" --password-stdin
            docker pull $DH_USER/task-backend:$BUILD_NUMBER
            docker pull $DH_USER/task-frontend:$BUILD_NUMBER
            docker logout

            # Replace the app containers
            docker rm -f prod-backend prod-frontend || true
            docker run -d --name prod-backend --network prod-net --restart unless-stopped \
              -e DB_HOST=prod-db -e DB_NAME -e DB_USER -e DB_PASSWORD \
              $DH_USER/task-backend:$BUILD_NUMBER
            docker run -d --name prod-frontend --network prod-net --restart unless-stopped \
              -e BACKEND_URL=http://prod-backend:5000 -p 8001:8000 \
              $DH_USER/task-frontend:$BUILD_NUMBER

            # Smoke test
            for i in $(seq 1 30); do
              docker run --rm --network prod-net curlimages/curl -sf \
                http://prod-frontend:8000/ >/dev/null && exit 0
              sleep 2
            done
            docker logs prod-backend
            docker logs prod-frontend
            exit 1
          '''
        }
      }
    }
    stage('SBOM') {
      steps {
        sh '''
          for img in task-backend task-frontend; do
            docker run --rm \
              -v /var/run/docker.sock:/var/run/docker.sock \
              -v trivy-cache:/root/.cache \
              --volumes-from jenkins -w "$WORKSPACE" \
              aquasec/trivy:latest image \
              --format cyclonedx --output sbom-$img.cdx.json \
              $img:${BUILD_NUMBER}
          done
        '''
      }
    }
  }

  post {
    always {
      sh '''
        docker rm -f zap-$BUILD_NUMBER frontend-$BUILD_NUMBER \
          backend-$BUILD_NUMBER db-$BUILD_NUMBER || true
        docker network rm net-$BUILD_NUMBER || true
        docker volume rm zap-wrk-$BUILD_NUMBER || true
      '''
      archiveArtifacts artifacts: 'zap-report.html, sbom-*.json', allowEmptyArchive: true
    }
  }
}