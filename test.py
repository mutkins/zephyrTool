import json

import requests
from operator import itemgetter, attrgetter, methodcaller
import datetime
import time
# import array
cycleId = 901
project = 13781
headers = {
    "Content-Type": "application/json;charset='utf-8'",
    "Authorization": "Basic TXV0a2luOncxZjVpUDU2"
}
#Формируем get запрос для получения всех циклов проекта
url = "https://jira.blogic.ru/rest/zapi/latest/cycle?projectId="+str(project)+"&versionId=&id=&offset=&issueId=&expand="
cyclesByProject = requests.get(url=url, headers=headers)
json = cyclesByProject.json()
json2 = json['18519']
json3 = json.get('18519')
for i in json:
    print(i)
    # for k in range(len()):
    print(json2)
