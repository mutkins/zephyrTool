import main
import schedule
import time
import datetime

def job():
    main.runZTool()
    print(f"I've done {datetime.datetime.now()}")


schedule.every(30).minutes.do(job)

while True:
    schedule.run_pending()
    time.sleep(1)
