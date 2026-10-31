pipeline {
    agent any
    environment {
        IMAGE_NAME = "DOCKERHUB_USERNAME/taskflow"
        K8S_NAMESPACE = "default"
    }
    stages {
        stage('Checkout') {
            steps { checkout scm }
        }
        stage('Install & Test') {
            steps {
                bat 'python -m pip install -r requirements.txt'
                bat 'python -m pytest -v'
            }
        }
        stage('Build Docker Image') {
            steps {
                bat 'docker build -t %IMAGE_NAME%:%BUILD_NUMBER% -t %IMAGE_NAME%:latest .'
            }
        }
        stage('Push Docker Image') {
            when { expression { return env.DOCKERHUB_CREDENTIALS_ID?.trim() } }
            steps {
                withCredentials([usernamePassword(credentialsId: env.DOCKERHUB_CREDENTIALS_ID,
                    usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                    bat 'docker login -u %DOCKER_USER% -p %DOCKER_PASS%'
                    bat 'docker push %IMAGE_NAME%:%BUILD_NUMBER%'
                    bat 'docker push %IMAGE_NAME%:latest'
                    bat 'docker logout'
                }
            }
        }
        stage('Deploy to Kubernetes') {
            when { expression { return env.KUBECONFIG_CREDENTIALS_ID?.trim() && env.DOCKERHUB_CREDENTIALS_ID?.trim() } }
            steps {
                withCredentials([file(credentialsId: env.KUBECONFIG_CREDENTIALS_ID, variable: 'KUBECONFIG')]) {
                    bat 'kubectl apply -f k8s/'
                    bat 'kubectl set image deployment/taskflow taskflow=%IMAGE_NAME%:%BUILD_NUMBER% -n %K8S_NAMESPACE%'
                    bat 'kubectl rollout status deployment/taskflow -n %K8S_NAMESPACE% --timeout=120s'
                }
            }
        }
    }
    post {
        always { echo 'TaskFlow CI/CD pipeline finished. Check stage results above.' }
    }
}
