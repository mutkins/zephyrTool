pipeline {
    agent any
    stages {
        stage('version'){
            steps {
                bat 'python --version'
                   }
        }
        stage('main'){
            steps {
                bat 'python start.py'
                   }
        }
    }
}
