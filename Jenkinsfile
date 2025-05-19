pipeline {
    agent any

    environment {
        BACKEND_IMAGE = 'prajyotshende/movie-recc-server:latest'
        FRONTEND_IMAGE = 'prajyotshende/movie-recc-client:latest'
        MLSERVICE_IMAGE = 'prajyotshende/movie-recc-ml-service:latest'
        GITHUB_REPO_URL = 'https://github.com/prajyotshende/MLOps_MovieReccSys.git'
    }

    stages {
        stage('Checkout') {
            steps {
                script {
                    git branch: 'main', url: "${GITHUB_REPO_URL}"
                }
            }
        }

        stage('Build Docker Images') {
            steps {
                script {
                    sh 'docker build -t $FRONTEND_IMAGE ./client'
                    sh 'docker build -t $BACKEND_IMAGE ./server'
                    sh 'docker build -t $MLSERVICE_IMAGE ./ml'
                }
            }
        }

        stage('Push Docker Images') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'DockerHubCred', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                    script {
                        def loginStatus = sh(script: 'echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin', returnStatus: true)
                        if (loginStatus != 0) {
                            error("Docker login failed. Check credentials and try again.")
                        }

                        sh "docker push $FRONTEND_IMAGE"
                        sh "docker push $BACKEND_IMAGE"
                        sh "docker push $MLSERVICE_IMAGE"
                    }
                }
            }
        }

        // ---- Uncomment this to use Docker Compose deployment ----
        /*
        stage('Run Ansible Playbook for Docker Compose') {
            steps {
                script {
                    sh '''
                        ansible-playbook -vvv compose/deploy.yaml
                    '''
                }
            }
        }
        */

        // ---- Active: Kubernetes Ansible Deployment ----
        stage('Run Ansible Playbook for Kubernetes') {
            steps {
                script {
                    sh '''
                        ansible-playbook -vvv k8s/deploy.yaml
                    '''
                }
            }
        }

    }

    post {
        success {
            echo "Deployment pipeline completed successfully."
        }
        failure {
            echo "Pipeline failed. Please check logs above."
        }
    }
}
