def projectName = 'final-hack-trial-2'
def version = "0.0.${currentBuild.number}"
def dockerImageTag = "${projectName}:${version}"

pipeline {
  agent any
  stages {
    stage('Build Container') {
      steps {
        sh "docker build -t ${dockerImageTag} --build-arg PYTHON_MAIN_FILE=app.py ."
      }
    }

    stage('Deploy Container To Openshift') {
      steps {
        sh "oc login https://localhost:8443 --username admin --password admin --insecure-skip-tls-verify=true"
        sh "oc project ${projectName} || oc new-project ${projectName}"
        sh "oc get service mongo || oc new-app mongo"
        sh "oc delete all --selector app=${projectName} || echo 'Unable to delete all previous openshift resources'"
        sh "oc new-app ${dockerImageTag} -l version=${version}"
        sh "oc expose svc/${projectName}"
      }
    }
  }
}