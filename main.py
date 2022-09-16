import os
import requests
from operator import itemgetter
import datetime
import time
import logging
import sys
import base64
from dotenv import load_dotenv

load_dotenv()
projectId = 13781
logging.basicConfig(filename="main.log", level=logging.DEBUG, filemode="w")
log = logging.getLogger("main")

# Вытягиваем из переменных среды логин и пароль, превращаем их в Base64 строку
usernameAndPassString = f"{os.environ.get('USER')}:{os.environ.get('PASSWORD')}"
usernameAndPassByte = usernameAndPassString.encode("UTF-8")
usernameAndPassByteBase64 = base64.b64encode(usernameAndPassByte)
usernameAndPassStringBase64 = usernameAndPassByteBase64.decode("UTF-8")

headers = {
    "Content-Type": "application/json;charset='utf-8'",
    "Authorization": f"Basic {usernameAndPassStringBase64}"
}


# Функция для отправки REST запросов, чтобы каждый раз не писать все эти try except

def sendRESTRequest(reqtype, url_, headers_, body_=""):
    print(f"SEND_{reqtype}_REQUEST url={url_}, headers: {headers_}")
    log.info(f"SEND_{reqtype}_REQUEST url={url_}, headers: {headers_}")
    try:
        if reqtype == "GET":
            res = requests.get(url=url_, headers=headers_)
        elif reqtype == "PUT":
            res = requests.put(url=url_, headers=headers_, json=body_)
        else:
            res = f"Неподдерживаемый тип запроса {reqtype}"
            print(res)
            log.error(res)
            sys.exit(1)
    except requests.exceptions.RequestException as e:
        print("HTTP_Error: ", e)
        log.exception(f"HTTP_Error:{e}")
        sys.exit(1)
    print(f"RESPONSE: STATUS_CODE {res.status_code}")
    if res.status_code == 200:
        log.info(f"RESPONSE: STATUS_CODE {res.status_code}")
    else:
        log.error(f"RESPONSE: STATUS_CODE {res.status_code}")
        sys.exit(1)
    log.debug(f"RESPONCE_TEXT: {res.text}")
    return res

# Отправляем get запрос для получения всех циклов проекта
url = f"https://jira.blogic.ru/rest/zapi/latest/cycle?projectId={projectId}&versionId=&id=&offset=&issueId=&expand="
cyclesByProject = sendRESTRequest("GET", url, headers)

# Разбираем json, ищем все циклы с именем SUMMARY

summaryCyclesList = []
n = 0
try:
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

except Exception as e:
    print(f"JSON_DECODE_ERROR: {e}")
    log.exception(f"JSON_DECODE_ERROR: {e}")
    sys.exit(1)
print(f"JSON_IS_DECODED_SUCCESSFUL, [cycle,version]:{summaryCyclesList}")
log.info(f"JSON_IS_DECODED_SUCCESSFUL, [cycle,version]:{summaryCyclesList}")

# Для каждого цикла SUMMARY отправляем get запрос для получения его выполнений в рамках этой версии
for cycleId, versionId in summaryCyclesList:
    url = f"https://jira.blogic.ru/rest/zapi/latest/execution?issueId=&projectId=&versionId={versionId}&offset=&action=&sorter=&expand=&limit=&folderId=&limit=1000&cycleId={cycleId}"
    summaryCycle = sendRESTRequest("GET", url, headers)

    # Парсим полученный JSON, разбираем каждое выполнение в SUMMARY
    try:
        executionsDict = summaryCycle.json().get('executions')
    except Exception as e:
        print(f"JSON_DECODE_ERROR: {e}")
        log.exception(f"JSON_DECODE_ERROR: {e}")
        sys.exit()
    for i in executionsDict:
        try:
            issueId = i.get('issueId')
            executionId = i.get('id')
        except Exception as e:
            print(f"JSON_DECODE_ERROR: {e}")
            log.exception(f"JSON_DECODE_ERROR: {e}")
            sys.exit(1)
        # У каждого выполнения взяли номер теста и запрашиваем все его выполнения в рамках данной версии
        url = f"https://jira.blogic.ru/rest/zapi/latest/execution?issueId={issueId}&projectId=&versionId={versionId}&offset=&action=&sorter=&expand=&limit=&folderId=&limit=1000&cycleId="
        executionsByIssueId = sendRESTRequest("GET", url, headers)

        # Разбираем каждое выполнение этого теста
        executionsByIssueIdList = []
        m = 0
        for k in executionsByIssueId.json().get('executions'):
            try:
                # Фильтруем выполнения из цикла SUMMARY (чтобы случайно не считать статус выполнения из него)
                if str(k.get('cycleId')) != cycleId:
                    log.info(f"Executions id: {k.get('id')}")
                    # Из каждого выполнения берем id, статус и дату создания, составляем из них список
                    executionsByIssueIdList.append([])
                    executionsByIssueIdList[m].append(k.get('id'))
                    executionsByIssueIdList[m].append(k.get('issueId'))
                    executionsByIssueIdList[m].append(k.get('executionStatus'))
                    executionsByIssueIdList[m].append(k.get('createdOn'))
                    # дату в unix переводим, чтобы сортировать потом проще было
                    uTime = time.mktime(datetime.datetime.strptime(k.get('createdOn'),
                                                                   "%d.%m.%Y %H:%M").timetuple())
                    executionsByIssueIdList[m].append(uTime)
                    m = m + 1
            except Exception as e:
                print(f"JSON_DECODE_ERROR: {e}")
                log.exception(f"JSON_DECODE_ERROR: {e}")
                sys.exit(1)
        print(
            f"JSON_IS_DECODED_SUCCESSFUL, [executionId, issueId,executionStatus,createdOn,uTime]:{executionsByIssueIdList}")
        log.info(
            f"JSON_IS_DECODED_SUCCESSFUL, [executionId, issueId,executionStatus,createdOn,uTime]:{executionsByIssueIdList}")

        # сортируем полученный список по unix дате по убыванию
        executionsByIssueIdSortedList = sorted(executionsByIssueIdList, key=itemgetter(4), reverse=True)
        finalExecutionStatus = executionsByIssueIdSortedList[0][2]
        log.info(
            f"Cycle = {cycleId}, versionId={versionId}, lastExecutionCreated in {executionsByIssueIdSortedList[0][3]}, lastExecutionStatus={finalExecutionStatus}")

        # Теперь мы знаем статус последнего выполнения этого теста, проставляем этот статус в это выполнение в цикле SUMMARY
        url = f"https://jira.blogic.ru/rest/zapi/latest/execution/{executionId}/execute"
        body = {
            "status": finalExecutionStatus
        }
        sendRESTRequest("PUT", url, headers, body)
