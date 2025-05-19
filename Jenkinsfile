pipeline {
    agent any

    environment {
        BACKEND_IMAGE = 'prajyotshende/movie-recc-server:latest'
        FRONTEND_IMAGE = 'prajyotshende/movie-recc-client:latest'
        MLSERVICE_IMAGE = 'prajyotshende/movie-recc-ml-service:latest'
        GITHUB_REPO_URL = 'https://github.com/RakshitPatel910/MLOps_MovieReccSys.git'
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
                withCredentials([usernamePassword(credentialsId: 'docker-id', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
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
        
            stage('Ansible Deploy K8s') {
                        steps {
                            withCredentials([
                                usernamePassword(credentialsId: 'ansible-id',
                                                usernameVariable: 'ANSIBLE_USER',
                                                passwordVariable: 'ANSIBLE_SSH_PASS'),
                                string(credentialsId: 'vault-pass',
                                    variable: 'VAULT_PASS')
                            ]) {
                                writeFile file: 'ansible/.vault_pass.txt', text: VAULT_PASS

                                sh '''
                                    export ANSIBLE_HOST_KEY_CHECKING=False

                                    ansible-playbook \
                                    -i ansible/inventory.ini \
                                    ansible/playbook-k8s.yml \
                                    -e ansible_user=$ANSIBLE_USER \
                                    -e ansible_ssh_pass=$ANSIBLE_SSH_PASS \
                                    --vault-password-file ansible/.vault_pass.txt
                                '''

                                sh 'rm -f ansible/.vault_pass.txt'
                            }
                        }
                    }

        

        // ---- Active: Kubernetes Ansible Deployment ----
        // stage('Ansible Deploy Compose') {
        //     steps {
        //         withCredentials([
        //         usernamePassword(credentialsId: 'ansible-id',
        //                         usernameVariable: 'ANSIBLE_USER',
        //                         passwordVariable: 'ANSIBLE_SSH_PASS'),
        //         string(credentialsId: 'vault-pass', variable: 'VAULT_PASS')
        //         ]) {
        //         // write out a one-time vault-pw file
        //         writeFile file: 'ansible/.vault_pass.txt', text: VAULT_PASS

        //         sh '''
        //             export ANSIBLE_HOST_KEY_CHECKING=False

        //             ansible-playbook \
        //             -i ansible/inventory.ini \
        //             ansible/playbook-compose.yml \
        //             -e ansible_user=$ANSIBLE_USER \
        //             -e ansible_ssh_pass=$ANSIBLE_SSH_PASS \
        //             --vault-password-file ansible/.vault_pass.txt
        //         '''
        //         sh 'rm -f ansible/.vault_pass.txt'
        //         }
        //     }
        //     }


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
