pipeline {
    agent any
    environment {
                JIRA = credentials('6c0d6ec2-adb4-4f01-87a7-ed531447fa0d')
            }
    stages {
        stage('echo'){
            steps {
                echo "JIRA USERRRRR ${JIRA_USR}"
                   }
        }
       stage('runZtool'){
            steps {
                bat 'python jenkinsStart.py'
                   }
        }
    }
}
