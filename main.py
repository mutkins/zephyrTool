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
for i in cyclesByProject.json():
    for k in i:
        print(k)

# Формируем get запрос для получения цикла SUMMARY
url = "https://jira.blogic.ru/rest/zapi/latest/execution?issueId=&projectId=&versionId=&offset=&action=&sorter=&expand=&limit=&folderId=&limit=1000&cycleId="+str(cycleId)
summaryCycle = requests.get(url=url, headers=headers)

# Парсим полученный JSON, разбираем каждое выполнение в SUMMARY
for i in summaryCycle.json().get('executions'):
    issueId = i.get('issueId')
    executionID = i.get('id')
    print(issueId)
    # У каждого выполнения взяли номер теста и запрашиваем все его выполнения
    url = "https://jira.blogic.ru/rest/zapi/latest/execution?issueId="+str(issueId)+"&projectId=&versionId=&offset=&action=&sorter=&expand=&limit=&folderId=&limit=1000&cycleId="
    executionsByIssueId = requests.get(url=url, headers=headers)
    # array.array()
    executionsByIssueIdList = []
    m = 0
    # Разбираем каждое выполнение этого теста
    for k in executionsByIssueId.json().get('executions'):

        if k.get('cycleId') != cycleId: # Фильтруем выполнения из цикла SUMMARY (чтобы случайно не считать статус выполнения из него)

            # Из каждого выполнения берем id, статус и дату создания, составляем из них список
            executionsByIssueIdList.append([])
            executionsByIssueIdList[m].append(k.get('id'))
            executionsByIssueIdList[m].append(k.get('executionStatus'))
            executionsByIssueIdList[m].append(k.get('createdOn'))
            uTime = time.mktime(datetime.datetime.strptime(k.get('createdOn'), "%d.%m.%Y %H:%M").timetuple()) # дату в unix переводим, чтобы сортировать потом проще было
            executionsByIssueIdList[m].append(uTime)
            m = m + 1
    #отладка
    # for l in executionsByIssueIdList:
    #     print(l)

    #     сортируем полученный список по unix дате по убыванию
    executionsByIssueIdSortedList = sorted(executionsByIssueIdList, key=itemgetter(3), reverse=True)
    finalExecutionStatus = executionsByIssueIdSortedList[0][1]

    #  отладка
    # print("NOW SORTED LIST")
    # for l in executionsByIssueIdSortedList:
    #     print(l)
    # print("FINNALY", executionsByIssueIdSortedList[0][1])

    # Теперь мы знаем статус последнего выполнения этого теста, проставляем этот статус в цикле SUMMARY
    url = "https://jira.blogic.ru/rest/zapi/latest/execution/"+str(executionID)+"/execute"
    body = {
        "status": finalExecutionStatus
    }
    res = requests.put(url=url, headers=headers, json=body)
    print(res.status_code)
