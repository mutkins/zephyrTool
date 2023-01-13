pipeline {
    agent any
    environment {
                JIRA = credentials('6c0d6ec2-adb4-4f01-87a7-ed531447fa0d')
                TOKEN = credentials('botID')
                CHAT_ID = credentials('chatID')
            }
    stages {
       stage('runZtool'){
            steps {
                bat 'python jenkinsStart.py'
                   }
        }
    }
    post {
        failure {
        bat  ("""
            curl -s -X POST https://api.telegram.org/bot${TOKEN}/sendMessage -d chat_id=${CHAT_ID} -d parse_mode=markdown -d text="*${env.JOB_NAME}* FAILED ${env.BUILD_URL}"
        """)
        }
        aborted {
        bat  ("""
            curl -s -X POST https://api.telegram.org/bot${TOKEN}/sendMessage -d chat_id=${CHAT_ID} -d parse_mode=markdown -d text="*${env.JOB_NAME}* ABORTED ${env.BUILD_URL}"
        """)
        }

    }



}
