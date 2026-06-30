pipeline {
    agent any

    environment {
        DOCKER_HUB_CREDENTIALS = credentials('dockerhub-dumindu-credentials')
        DOCKER_IMAGE           = 'beliver247/greendevops-dashboard'
        DOCKER_TAG             = "${BUILD_NUMBER}"

        REMOTE_HOST            = '147.15.144.192'
        REMOTE_PORT            = '2510'
        REMOTE_USER            = 'dumindu'
        SSH_CREDENTIALS        = 'ubuntu-pc-ssh-dumindu'
    }

    stages {
        stage('Checkout') {
            steps {
                echo "Checking out Dashboard from GitHub..."
                checkout scm
            }
        }

        stage('Docker Build') {
            steps {
                echo "Building Dashboard Docker image: ${DOCKER_IMAGE}:${DOCKER_TAG}"
                sh "docker build --platform linux/amd64 -t ${DOCKER_IMAGE}:${DOCKER_TAG} -t ${DOCKER_IMAGE}:latest ."
            }
        }

        stage('Docker Push') {
            steps {
                echo "Pushing image to Docker Hub..."
                sh """
                    echo "${DOCKER_HUB_CREDENTIALS_PSW}" | docker login -u "${DOCKER_HUB_CREDENTIALS_USR}" --password-stdin
                    docker push ${DOCKER_IMAGE}:${DOCKER_TAG}
                    docker push ${DOCKER_IMAGE}:latest
                    docker logout
                """
            }
        }

        stage('Deploy Locally (Jenkins Server)') {
            steps {
                echo "Deploying dashboard locally on the Jenkins server..."
                sh """
                    docker-compose down || true
                    docker-compose up -d
                    sleep 5
                    docker-compose ps
                """
            }
        }
    }

    post {
        always {
            sh "docker rmi ${DOCKER_IMAGE}:${DOCKER_TAG} || true"
            sh "docker image prune -f || true"
        }
        success {
            echo "Dashboard Deployment SUCCESSFUL"
        }
        failure {
            echo "Dashboard Deployment FAILED"
        }
    }
}
