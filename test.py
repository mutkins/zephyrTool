import sys
import json
import requests
import logging

logging.basicConfig(filename="sample.log", level=logging.INFO, filemode="w")
log = logging.getLogger("main")

projectId = 13781
headers = {
    "Content-Type": "application/json;charset='utf-8'",
    "Authorization": "Basic TXV0a2luOncxZjVpUDU2"
}
#test
# Формируем get запрос для получения всех циклов проекта
url = f"https://jira.blogic.ru/rest/zapi/latest/cycle?projectId={projectId}&versionId=&id=&offset=&issueId=&expand="
print(f"SEND GET REQUEST url={url}, headers: {headers}")
log.info(f"SEND GET REQUEST url={url}, headers: {headers}")
try:
    cyclesByProject = requests.get(url=url, headers=headers)
except requests.exceptions.RequestException as e:
    print("HTTP_Error: ", e)
    log.exception(f"HTTP_Error:{e}")
    sys.exit()
print(f"RESPONSE: STATUS_CODE {cyclesByProject.status_code}")
log.info(f"RESPONSE: STATUS_CODE {cyclesByProject.status_code}, text: {cyclesByProject.text}")

# Разбираем json, ищем все циклы с именем SUMMARY
try:
    jsonDict = cyclesByProject.json()
    summaryCyclesList = []
    n = 0
    for item in jsonDict.items():
        for childItem in item[1]:
            for finallyItem in childItem.items():
                # Прежде чем проверять наличие имени SUMMARY, проверим, что этот элемент - словарь (чтобы ненароком не применить get к int)
                if isinstance(finallyItem[1], dict) and finallyItem[1].get('name') == "SUMMARY":
                    # Записываем в список номер цикла и версию
                    summaryCyclesList.append([])
                    summaryCyclesList[n].append(finallyItem[0])
                    summaryCyclesList[n].append(finallyItem[1].get('versionId'))
                    n = n+1
except:
    print(f"JSON_DECODE_ERROR:")
    log.exception(f"JSON_DECODE_ERROR:")
    sys.exit()
print(f"JSON IS DECODED SUCCESSFUL, [cycle,version]:{summaryCyclesList}")
log.info(f"JSON IS DECODED SUCCESSFUL, [cycle,version]:{summaryCyclesList}")
for cycleId, versionId in summaryCyclesList:
    print(cycleId, versionId)
