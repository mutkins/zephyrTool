import main
import schedule
import time
import datetime

lastStatus = 0
def job():
    lastStatus = main.runZTool()

    if lastStatus:
        print(f"Fail {datetime.datetime.now()}, next try in 5 minutes")
        time.sleep(300)
        job()
    else:
        print(f"Success {datetime.datetime.now()}")



schedule.every(15).minutes.do(job)

while True:
    schedule.run_pending()
    time.sleep(1)
