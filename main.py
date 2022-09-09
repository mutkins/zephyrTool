import requests
from operator import itemgetter, attrgetter, methodcaller
import datetime
import time
import logging
import sys

logging.basicConfig(filename="main.log", level=logging.INFO, filemode="w")
log = logging.getLogger("main")

headers = {
    "Content-Type": "application/json;charset='utf-8'",
    "Authorization": "Basic TXV0a2luOncxZjVpUDU2"
}
projectId = 13781

# Отправляем get запрос для получения всех циклов проекта
url = f"https://jira.blogic.ru/rest/zapi/latest/cycle?projectId={projectId}&versionId=&id=&offset=&issueId=&expand="
print(f"SEND_GET_REQUEST url={url}, headers: {headers}")
log.info(f"SEND_GET_REQUEST url={url}, headers: {headers}")

try:
    cyclesByProject = requests.get(url=url, headers=headers)
except requests.exceptions.RequestException as e:
    print("HTTP_Error: ", e)
    log.exception(f"HTTP_Error:{e}")
    sys.exit()
print(f"RESPONSE: STATUS_CODE {cyclesByProject.status_code}")
if cyclesByProject.status_code == 200:
    log.info(f"RESPONSE: STATUS_CODE {cyclesByProject.status_code}")
else:
    log.error(f"RESPONSE: STATUS_CODE {cyclesByProject.status_code}")
    sys.exit()
log.debug(f"RESPONCE_TEXT: {cyclesByProject.text}")

# Разбираем json, ищем все циклы с именем SUMMARY
try:
    summaryCyclesList = []
    n = 0
    for item in cyclesByProject.json().items():
        for childItem in item[1]:
            for finallyItem in childItem.items():
                # Прежде чем проверять наличие имени SUMMARY, проверим, что этот элемент - словарь (чтобы ненароком не применить get к int)
                if isinstance(finallyItem[1], dict) and finallyItem[1].get('name') == "SUMMARY":
                    # Записываем в список номер цикла и версию
                    summaryCyclesList.append([])
                    summaryCyclesList[n].append(finallyItem[0])
                    summaryCyclesList[n].append(finallyItem[1].get('versionId'))
                    n = n + 1
except:
    print(f"JSON_DECODE_ERROR:")
    log.exception(f"JSON_DECODE_ERROR:")
    sys.exit()
print(f"JSON_IS_DECODED_SUCCESSFUL, [cycle,version]:{summaryCyclesList}")
log.info(f"JSON_IS_DECODED_SUCCESSFUL, [cycle,version]:{summaryCyclesList}")

# Для каждого цикла SUMMARY отправляем get запрос для получения его выполнений
for cycleId, versionId in summaryCyclesList:
    url = f"https://jira.blogic.ru/rest/zapi/latest/execution?issueId=&projectId=&versionId={versionId}&offset=&action=&sorter=&expand=&limit=&folderId=&limit=1000&cycleId={cycleId}"
    print(f"SEND_GET_REQUEST url={url}, headers: {headers}")
    log.info(f"SEND_GET_REQUEST url={url}, headers: {headers}")
    try:
        summaryCycle = requests.get(url=url, headers=headers)
    except requests.exceptions.RequestException as e:
        print("HTTP_Error: ", e)
        log.exception(f"HTTP_Error:{e}")
        sys.exit()
    print(f"RESPONSE: STATUS_CODE {summaryCycle.status_code}")
    if summaryCycle.status_code == 200:
        log.info(f"RESPONSE: STATUS_CODE {summaryCycle.status_code}")
    else:
        log.error(f"RESPONSE: STATUS_CODE {summaryCycle.status_code}")
        sys.exit()
    log.debug(f"RESPONCE_TEXT: {summaryCycle.text}")

    # Парсим полученный JSON, разбираем каждое выполнение в SUMMARY
    try:
        executionsDict = summaryCycle.json().get('executions')
    except:
        print(f"JSON_DECODE_ERROR:")
        log.exception(f"JSON_DECODE_ERROR:")
        sys.exit()
    for i in executionsDict:
        issueId = i.get('issueId')
        executionId = i.get('id')
        # У каждого выполнения взяли номер теста и запрашиваем все его выполнения в рамках данной версии
        url = f"https://jira.blogic.ru/rest/zapi/latest/execution?issueId={issueId}&projectId=&versionId={versionId}&offset=&action=&sorter=&expand=&limit=&folderId=&limit=1000&cycleId="
        executionsByIssueId = requests.get(url=url, headers=headers)
        executionsByIssueIdList = []
        m = 0
        # Разбираем каждое выполнение этого теста
        for k in executionsByIssueId.json().get('executions'):
            if str(k.get('cycleId')) != cycleId:  # Фильтруем выполнения из цикла SUMMARY (чтобы случайно не считать статус выполнения из него)
                log.info(f"Executions id: {k.get('id')}")
                # Из каждого выполнения берем id, статус и дату создания, составляем из них список
                executionsByIssueIdList.append([])
                executionsByIssueIdList[m].append(k.get('id'))
                executionsByIssueIdList[m].append(k.get('issueId'))
                executionsByIssueIdList[m].append(k.get('executionStatus'))
                executionsByIssueIdList[m].append(k.get('createdOn'))
                uTime = time.mktime(datetime.datetime.strptime(k.get('createdOn'),
                                                               "%d.%m.%Y %H:%M").timetuple())  # дату в unix переводим, чтобы сортировать потом проще было
                executionsByIssueIdList[m].append(uTime)
                m = m + 1
        print(f"JSON_IS_DECODED_SUCCESSFUL, [executionId, issueId,executionStatus,createdOn,uTime]:{executionsByIssueIdList}")
        log.info(f"JSON_IS_DECODED_SUCCESSFUL, [executionId, issueId,executionStatus,createdOn,uTime]:{executionsByIssueIdList}")

        # сортируем полученный список по unix дате по убыванию
        executionsByIssueIdSortedList = sorted(executionsByIssueIdList, key=itemgetter(4), reverse=True)
        finalExecutionStatus = executionsByIssueIdSortedList[0][2]
        log.info(f"Cycle = {cycleId}, versionId={versionId}, lastExecutionCreated in {executionsByIssueIdSortedList[0][3]}, lastExecutionStatus={finalExecutionStatus}")

        # Теперь мы знаем статус последнего выполнения этого теста, проставляем этот статус в это выполнение в цикле SUMMARY
        url = f"https://jira.blogic.ru/rest/zapi/latest/execution/{executionId}/execute"
        body = {
            "status": finalExecutionStatus
        }
        print(f"SEND_PUT_REQUEST url={url}, headers: {headers}")
        log.info(f"SEND_PUT_REQUEST url={url}, headers: {headers}")
        try:
            setStatusToExecute = requests.put(url=url, headers=headers, json=body)
        except requests.exceptions.RequestException as e:
            print("HTTP_Error: ", e)
            log.exception(f"HTTP_Error:{e}")
            sys.exit()
        print(f"RESPONSE: STATUS_CODE {setStatusToExecute.status_code}")
        if setStatusToExecute.status_code == 200:
            log.info(f"RESPONSE: STATUS_CODE {setStatusToExecute.status_code}")
        else:
            log.error(f"RESPONSE: STATUS_CODE {setStatusToExecute.status_code}")
            log.debug(f"RESPONCE_TEXT: {setStatusToExecute.text}")
            sys.exit()
