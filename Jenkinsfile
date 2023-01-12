pipeline {
    agent any
    stages {
    stage('echo'){
            enviroment{
                JIRA = credentials('6c0d6ec2-adb4-4f01-87a7-ed531447fa0d')
            }
            steps {
                echo "JIRA USERRRRR ${JIRA_USR}"
                   }
        }
       stage('runZtool'){
            enviroment{
                JIRA = credentials('6c0d6ec2-adb4-4f01-87a7-ed531447fa0d')
            }
            steps {
                bat 'python jenkinsStart.py'
                   }
        }
    }
}
