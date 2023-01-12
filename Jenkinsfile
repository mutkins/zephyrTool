pipeline {
    agent any
    stages {
        stage('version'){
            steps {
                bat 'python3 --version'
                   }
        }
        stage('main'){
            steps {
                bat 'python3 main.py'
                   }
        }
    }
}
