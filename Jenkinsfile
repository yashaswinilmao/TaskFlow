
pipeline {
    agent any

    environment {
        IMAGE_NAME = "yashaswiniakula/taskflow"
        K8S_NAMESPACE = "default"
        DOCKERHUB_CREDENTIALS_ID = "dockerhub-credentials"
        KUBECONFIG_CREDENTIALS_ID = "kubeconfig"
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Install & Test') {
            steps {
                bat '"C:\\Users\\Akula yashaswini\\AppData\\Local\\Programs\\Python\\Python313\\python.exe" -m pip install -r requirements.txt'

                bat '"C:\\Users\\Akula yashaswini\\AppData\\Local\\Programs\\Python\\Python313\\python.exe" -m pytest -v'
            }
        }

        stage('Build Docker Image') {
            steps {
                bat 'docker build -t %IMAGE_NAME%:%BUILD_NUMBER% -t %IMAGE_NAME%:latest .'
            }
        }

        stage('Push Docker Image') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: env.DOCKERHUB_CREDENTIALS_ID,
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    bat 'echo %DOCKER_PASS%| docker login -u %DOCKER_USER% --password-stdin'

                    bat 'docker push %IMAGE_NAME%:%BUILD_NUMBER%'

                    bat 'docker push %IMAGE_NAME%:latest'

                    bat 'docker logout'
                }
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                withCredentials([file(
                    credentialsId: env.KUBECONFIG_CREDENTIALS_ID,
                    variable: 'KUBECONFIG'
                )]) {
                    bat 'kubectl apply -f k8s/'

                    bat 'kubectl set image deployment/taskflow taskflow=%IMAGE_NAME%:%BUILD_NUMBER% -n %K8S_NAMESPACE%'

                    bat 'kubectl rollout status deployment/taskflow -n %K8S_NAMESPACE% --timeout=120s'
                }
            }
        }
    }

    post {
        always {
            echo 'TaskFlow CI/CD pipeline finished. Check stage results above.'
        }

        success {
            echo 'TaskFlow CI/CD Pipeline completed successfully!'
        }

        failure {
            echo 'TaskFlow CI/CD Pipeline failed. Check Console Output.'
        }
    }
}
