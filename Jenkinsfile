// AgriSmart AI — Jenkins CI/CD Pipeline
// Triggered on every push to the main branch.

pipeline {
    agent any

    environment {
        IMAGE_NAME     = "agrismart-api"
        TEST_IMAGE     = "agrismart-test"
        REGISTRY       = "your-dockerhub-username"      // change this
        BUILD_TAG      = "${IMAGE_NAME}:${BUILD_NUMBER}"
        LATEST_TAG     = "${IMAGE_NAME}:latest"
    }

    options {
        timestamps()
        timeout(time: 45, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    stages {

        // ── 1. Checkout ────────────────────────────
        stage('Checkout') {
            steps {
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: '*/main']],
                    userRemoteConfigs: [[
                        url: 'https://github.com/aayushspundir2007-dot/Agri-ai.git'
                    ]]
                ])
                echo "Checked out commit: ${GIT_COMMIT}"
            }
        }

        // ── 2. Environment setup ───────────────────
        stage('Environment Setup') {
            steps {
                sh 'docker info'
                sh '''
                    if [ ! -f .env ]; then
                        cp .env.example .env
                        echo "Created .env from .env.example"
                    fi
                '''
                sh 'mkdir -p reports'
            }
        }

        // ── 3. Build images ────────────────────────
        stage('Build Images') {
            parallel {
                stage('Build API image') {
                    steps {
                        sh "docker build -t ${IMAGE_NAME}:${BUILD_NUMBER} -t ${IMAGE_NAME}:latest ."
                        echo "Built ${IMAGE_NAME}:${BUILD_NUMBER}"
                    }
                }
                stage('Build test image') {
                    steps {
                        sh "docker build -f Dockerfile.test -t ${TEST_IMAGE}:${BUILD_NUMBER} ."
                        echo "Built ${TEST_IMAGE}:${BUILD_NUMBER}"
                    }
                }
            }
        }

        // ── 4. Unit tests ──────────────────────────
        stage('Unit Tests') {
            steps {
                sh """
                    docker run --rm \\
                        -v \$(pwd)/models:/app/models \\
                        -v \$(pwd)/reports:/app/reports \\
                        -v \$(pwd)/users.json:/app/users.json \\
                        ${TEST_IMAGE}:${BUILD_NUMBER} \\
                        pytest app/tests/unit/ -v --tb=short \\
                        -m unit \\
                        --junitxml=reports/unit-results.xml \\
                        --cov=app --cov-report=xml:reports/coverage.xml
                """
            }
            post {
                always {
                    junit 'reports/unit-results.xml'
                }
            }
        }

        // ── 5. Integration tests ───────────────────
        stage('Integration Tests') {
            steps {
                sh "docker-compose -f docker-compose.test.yml up --abort-on-container-exit"
                sh "docker-compose -f docker-compose.test.yml down"
                sh """
                    docker run --rm \\
                        -v \$(pwd)/models:/app/models \\
                        -v \$(pwd)/reports:/app/reports \\
                        -v \$(pwd)/users.json:/app/users.json \\
                        --network host \\
                        ${TEST_IMAGE}:${BUILD_NUMBER} \\
                        pytest app/tests/integration/ -v --tb=short \\
                        -m integration \\
                        --junitxml=reports/integration-results.xml
                """
            }
            post {
                always {
                    junit 'reports/integration-results.xml'
                    sh "docker-compose -f docker-compose.test.yml down || true"
                }
            }
        }

        // ── 6. E2E tests ───────────────────────────
        stage('E2E Tests') {
            steps {
                sh "docker-compose up -d api streamlit selenium"
                sh "sleep 15"   // wait for health checks
                sh """
                    docker run --rm \\
                        -v \$(pwd)/models:/app/models \\
                        -v \$(pwd)/reports:/app/reports \\
                        -v \$(pwd)/users.json:/app/users.json \\
                        --network host \\
                        ${TEST_IMAGE}:${BUILD_NUMBER} \\
                        pytest app/tests/e2e/ -v --tb=short \\
                        -m e2e \\
                        --junitxml=reports/e2e-results.xml
                """
            }
            post {
                always {
                    junit 'reports/e2e-results.xml'
                    sh "docker-compose down || true"
                }
            }
        }

        // ── 7. Coverage gate ───────────────────────
        stage('Coverage Gate') {
            steps {
                script {
                    def xml = readFile('reports/coverage.xml')
                    def matcher = xml =~ /line-rate="([\d.]+)"/
                    if (matcher) {
                        def rate = matcher[0][1].toFloat() * 100
                        echo "Coverage: ${rate.round(1)}%"
                        if (rate < 70) {
                            error "Coverage ${rate.round(1)}% is below 70% threshold"
                        }
                    }
                }
            }
        }

        // ── 8. Security scan ───────────────────────
        stage('Security Scan') {
            steps {
                sh """
                    docker run --rm \\
                        -v \$(pwd):/src \\
                        pipelinecomponents/bandit:latest \\
                        bandit -r /src/app/ -f json -o /src/reports/security.json \\
                        --severity-level medium || true
                """
                script {
                    if (fileExists('reports/security.json')) {
                        def sec = readJSON file: 'reports/security.json'
                        def high = sec?.results?.findAll { it.issue_severity == 'HIGH' }
                        if (high && high.size() > 0) {
                            unstable("Security scan found ${high.size()} HIGH severity issues")
                        } else {
                            echo "Security scan: no HIGH severity issues"
                        }
                    }
                }
            }
        }

        // ── 9. Push to registry ────────────────────
        stage('Push to Registry') {
            when { branch 'main' }
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-creds',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh "echo ${DOCKER_PASS} | docker login -u ${DOCKER_USER} --password-stdin"
                    sh "docker tag ${IMAGE_NAME}:${BUILD_NUMBER} ${REGISTRY}/${IMAGE_NAME}:${BUILD_NUMBER}"
                    sh "docker tag ${IMAGE_NAME}:latest          ${REGISTRY}/${IMAGE_NAME}:latest"
                    sh "docker push ${REGISTRY}/${IMAGE_NAME}:${BUILD_NUMBER}"
                    sh "docker push ${REGISTRY}/${IMAGE_NAME}:latest"
                }
            }
        }

        // ── 10. Deploy ─────────────────────────────
        stage('Deploy') {
            when { branch 'main' }
            steps {
                sh "docker-compose down"
                sh "docker-compose up -d api streamlit frontend"
                sh "sleep 15"
                sh "curl -f http://localhost:8000/api/health || exit 1"
                echo "AgriSmart AI deployed successfully"
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'reports/**', allowEmptyArchive: true
            publishHTML([
                allowMissing: true,
                alwaysLinkToLastBuild: true,
                keepAll: true,
                reportDir: 'reports/coverage_html',
                reportFiles: 'index.html',
                reportName: 'Coverage Report'
            ])
        }
        success {
            echo "✅ Pipeline PASSED — AgriSmart AI v${BUILD_NUMBER} deployed"
        }
        failure {
            echo "❌ Pipeline FAILED — check test reports"
        }
        unstable {
            echo "⚠️  Pipeline UNSTABLE — security warnings detected"
        }
    }
}
