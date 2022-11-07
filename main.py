import os
import requests
from operator import itemgetter
import datetime
import time
import logging
import sys
import base64
from dotenv import load_dotenv
import pytz

load_dotenv()
projectId = 13781
logging.basicConfig(filename="main.log", level=logging.DEBUG, filemode="w", format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("main")

lastRunningStatus = 0
lastRunningDate = datetime.datetime.now(pytz.timezone('Asia/Yekaterinburg'))
report = []

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


def runZTool():
    # Отправляем get запрос для получения всех циклов проекта
    url = f"https://jira.blogic.ru/rest/zapi/latest/cycle?projectId={projectId}&versionId=&id=&offset=&issueId=&expand="
    cyclesByProject = sendRESTRequest("GET", url, headers)

    # Разбираем json, ищем все циклы с именем SUMMARY
    try:
        summaryCyclesList = []
        # Перебираем циклы в проекте, nс == number of cycle
        nc = 0
        for item in cyclesByProject.json().items():
            for childItem in item[1]:
                for finallyItem in childItem.items():
                    # Прежде чем проверять наличие имени SUMMARY, проверим, что этот элемент - словарь (чтобы ненароком не применить get к int)
                    if isinstance(finallyItem[1], dict) and finallyItem[1].get('name') == "SUMMARY":
                        # Записываем в список номер цикла и версию
                        summaryCyclesList.append([])
                        summaryCyclesList[nc].append(finallyItem[0])
                        summaryCyclesList[nc].append(finallyItem[1].get('versionId'))
                        summaryCyclesList[nc].append(finallyItem[1].get('versionName'))
                        nc = nc + 1

    except:
        print(f"JSON_DECODE_ERROR:")
        log.exception(f"JSON_DECODE_ERROR:")
        sys.exit(1)
    print(f"JSON_IS_DECODED_SUCCESSFUL, [cycle,version]:{summaryCyclesList}")
    log.info(f"JSON_IS_DECODED_SUCCESSFUL, [cycle,version]:{summaryCyclesList}")

    report.append(f"Найдено {len(summaryCyclesList)} циклов с именем SUMMARY [cycleId,versionId, versionName]: {summaryCyclesList}")

    # Теперь у нас есть список циклов SUMMARY, перебираем циклы по этому списку, nc - number of cycle
    nc = 0
    for cycleId, versionId, versionName in summaryCyclesList:

        # Отправляем get запрос для получения тестов, входящих в цикл
        url = f"https://jira.blogic.ru/rest/zapi/latest/execution?issueId=&projectId=&versionId={versionId}&offset=&action=&sorter=&expand=&limit=&folderId=&limit=1000&cycleId={cycleId}"
        summaryCycle = sendRESTRequest("GET", url, headers)

        # Парсим полученный JSON
        try:
            testsDict = summaryCycle.json().get('executions')
        except:
            print(f"JSON_DECODE_ERROR:")
            log.exception(f"JSON_DECODE_ERROR:")
            sys.exit()

        report.append(f"В цикле SUMMARY {summaryCyclesList[nc]} найдено {len(testsDict)} тестов")

        # Перебираем тесты (выполнения), входящие в цикл, t == test, nt == number of test
        nt = 0
        for t in testsDict:
            try:
                issueId = t.get('issueId')
                executionId = t.get('id')
                issueKey = t.get('issueKey')
            except:
                print(f"JSON_DECODE_ERROR:")
                log.exception(f"JSON_DECODE_ERROR:")
                sys.exit(1)

            # У каждого теста (выполнения) взяли номер и запрашиваем все его выполнения в рамках данной версии
            url = f"https://jira.blogic.ru/rest/zapi/latest/execution?issueId={issueId}&projectId=&versionId={versionId}&offset=&action=&sorter=&expand=&limit=&folderId=&limit=1000&cycleId="
            executionsByIssueId = sendRESTRequest("GET", url, headers)
            executionsDict = executionsByIssueId.json().get('executions')

            report.append(f"{nt + 1}. У теста {issueKey} найдено {len(executionsDict) - 1} выполнений в этой версии")

            # Разбираем каждое выполнение этого теста, e == execution, ne == number of execution
            executionsList = []
            ne = 0
            for e in executionsDict:
                try:
                    # Фильтруем выполнения из цикла SUMMARY (чтобы случайно не считать статус выполнения из него)
                    if str(e.get('cycleId')) != cycleId:
                        log.info(f"Executions id: {e.get('id')}")
                        # Из каждого выполнения берем id, статус и дату создания, составляем из них список
                        executionsList.append([])
                        executionsList[ne].append(e.get('id'))
                        executionsList[ne].append(e.get('issueId'))
                        executionsList[ne].append(e.get('executionStatus'))
                        executionsList[ne].append(e.get('createdOn'))
                        # дату в unix переводим, чтобы сортировать потом проще было
                        uTime = time.mktime(datetime.datetime.strptime(e.get('createdOn'),
                                                                       "%d.%m.%Y %H:%M").timetuple())
                        executionsList[ne].append(uTime)
                        # report.append(f"{nt + 1}.{ne + 1}. Выполнение {executionsList[ne][0]}, Статус {executionsList[ne][2]}, Дата создания выполнения {executionsList[ne][3]}")
                        ne = ne + 1
                except:
                    print(f"JSON_DECODE_ERROR:")
                    log.exception(f"JSON_DECODE_ERROR:")
                    sys.exit(1)
            print(
                f"JSON_IS_DECODED_SUCCESSFUL, [executionId, issueId,executionStatus,createdOn,uTime]:{executionsList}")
            log.info(
                f"JSON_IS_DECODED_SUCCESSFUL, [executionId, issueId,executionStatus,createdOn,uTime]:{executionsList}")

            # сортируем полученный список по unix дате по убыванию
            executionsByIssueIdSortedList = sorted(executionsList, key=itemgetter(4), reverse=True)
            finalExecutionId = executionsByIssueIdSortedList[0][0] if executionsByIssueIdSortedList else None
            finalExecutionStatus = executionsByIssueIdSortedList[0][2] if executionsByIssueIdSortedList else None
            finalExecutionDate = executionsByIssueIdSortedList[0][3] if executionsByIssueIdSortedList else None

            log.info(
                f"Cycle = {cycleId}, versionId={versionId}, lastExecutionCreated in {finalExecutionDate}, lastExecutionStatus={finalExecutionStatus}")
            report.append(f"Последнее выполнение - {finalExecutionId}, {finalExecutionDate}, Статус {finalExecutionStatus}")
            # Теперь мы знаем статус последнего выполнения этого теста, проставляем этот статус в это выполнение в цикле SUMMARY
            url = f"https://jira.blogic.ru/rest/zapi/latest/execution/{executionId}/execute"
            body = {
                "status": finalExecutionStatus
            }
            sendRESTRequest("PUT", url, headers, body)
            report.append(f"В версии {versionName} в выполнении теста {issueKey} установлен статус {finalExecutionStatus}")
            nt += 1
    log.info(f"REPORT: {report}")
    lastRunningDate = datetime.datetime.now(pytz.timezone('Asia/Yekaterinburg'))



def getLastRunningDate():
    return lastRunningDate


def getReport():
    return report

