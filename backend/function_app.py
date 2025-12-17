import logging
import azure.functions as func
import json
import traceback

# Try to import dictionary to allow detailed error reporting if imports fail
try:
    from src.main import app as fastapi_app
    from src.services.attendance_tasks import check_deadlines
    
    # Use AsgiFunctionApp to wrap FastAPI
    app = func.AsgiFunctionApp(app=fastapi_app, http_auth_level=func.AuthLevel.ANONYMOUS)

except Exception as e:
    logging.critical(f"Failed to load application: {e}", exc_info=True)
    error_detail = f"Application failed to start: {str(e)}\n{traceback.format_exc()}"
    
    # Create a dummy ASGI app that returns 500 with the error details
    async def error_app(scope, receive, send):
        if scope['type'] == 'http':
            await send({
                'type': 'http.response.start',
                'status': 500,
                'headers': [
                    [b'content-type', b'application/json'],
                ],
            })
            await send({
                'type': 'http.response.body',
                'body': json.dumps({
                    "error": "Startup Error", 
                    "message": "The application failed to initialize.",
                    "details": error_detail
                }).encode('utf-8'),
            })
        elif scope['type'] == 'lifespan':
            while True:
                message = await receive()
                if message['type'] == 'lifespan.startup':
                    await send({'type': 'lifespan.startup.complete'})
                elif message['type'] == 'lifespan.shutdown':
                    await send({'type': 'lifespan.shutdown.complete'})
                    return

    app = func.AsgiFunctionApp(app=error_app, http_auth_level=func.AuthLevel.ANONYMOUS)



# Timer Trigger: Runs every 30 minutes
@app.schedule(schedule="0 */30 * * * *", arg_name="timer", run_on_startup=False,
              use_monitor=False) 
async def schedule_attendance_reminder(timer: func.TimerRequest) -> None:
    if timer.past_due:
        logging.info('The timer is past due!')

    logging.info('Attendance Reminder Timer triggered.')
    
    try:
        # Check if check_deadlines is defined (it might not be if import failed)
        if 'check_deadlines' in globals():
            result = await check_deadlines()
            logging.info(f'Attendance Reminder Check completed: {result}')
        else:
             logging.error('check_deadlines function is not available due to startup error.')
    except Exception as e:
        logging.error(f'Error in Attendance Reminder Timer: {e}', exc_info=True)
    
    logging.info('Attendance Reminder Timer finished.')
