import logging
import azure.functions as func
from src.main import app as fastapi_app
# attendance_tasks will be implemented shortly
from src.services.attendance_tasks import check_deadlines

# Use AsgiFunctionApp to wrap FastAPI
# This allows Azure Functions to handle HTTP requests using the FastAPI app
app = func.AsgiFunctionApp(app=fastapi_app, http_auth_level=func.AuthLevel.ANONYMOUS)

@app.route(route="debug", auth_level=func.AuthLevel.ANONYMOUS)
async def debug_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    import json
    return func.HttpResponse(
        json.dumps({
            "status": "ok", 
            "message": "Function App is running",
            "url": req.url,
            "params": dict(req.params)
        }), 
        mimetype="application/json"
    )

# Timer Trigger: Runs every 30 minutes
# Schedule: "0 */30 * * * *" means every 30 minutes at 00, 30 seconds? No, standard cron is min hour day month year
# Azure cron: {second} {minute} {hour} {day} {month} {day-of-week}
# "0 */30 * * * *" -> At second 0, every 30th minute
@app.schedule(schedule="0 */30 * * * *", arg_name="timer", run_on_startup=False,
              use_monitor=False) 
async def schedule_attendance_reminder(timer: func.TimerRequest) -> None:
    if timer.past_due:
        logging.info('The timer is past due!')

    logging.info('Attendance Reminder Timer triggered.')
    
    try:
        # Execute the reminder logic
        result = await check_deadlines()
        logging.info(f'Attendance Reminder Check completed: {result}')
    except Exception as e:
        logging.error(f'Error in Attendance Reminder Timer: {e}', exc_info=True)
    
    logging.info('Attendance Reminder Timer finished.')
