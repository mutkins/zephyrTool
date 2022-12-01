import main
import schedule
import time
import datetime

lastStatus = 0
def job():
    lastStatus = main.runZTool()

    if lastStatus:
        print(f"Fail {datetime.datetime.now()}, next try in 1 minute")
        time.sleep(60)
        job()
    else:
        print(f"Success {datetime.datetime.now()}")



schedule.every(30).minutes.do(job)

while True:
    schedule.run_pending()
    time.sleep(1)
