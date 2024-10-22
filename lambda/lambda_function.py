import json
import logging
import traceback
from helper import Helper
from mongo_utils import MongoUtils
from telegram_message import TelegramMessage

logger = logging.getLogger(__name__)
logger.setLevel("INFO")


telegram_instance = TelegramMessage()
mongo_instance = MongoUtils()

def main():
    help = Helper()
    # status_mongo = mongo_instance.find_one(collection_name = 'garmin_status', query = {'date': help.sync_date,'isUpdated': True})
    # logger.info(f"Sync Status: {status_mongo}")
    # if not status_mongo:
    logger.info(f"Starting Execution")
    help.send_data_min()
    logger.info("Process Completed")
    return {'statusCode': 200, 'status': "OK"}
    # else:
    #     logger.info("Already Executed")              
    #     return {'statusCode': 200, 'status': "Already executed"}

def lambda_handler(event, context):
    try:
        response = main()
        return {'statusCode': 200, 'body': json.dumps(response)}
    except Exception as e:
        error_message = f"An error occurred: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        logger.error(error_message)
        telegram_instance.send_plain_message(chat_id=telegram_instance.config["TELEGRAM_CHAT_IDS"]["PAWAN"], text=error_message)
        return {'statusCode': 404, 'body': error_message} 
    
