from telegram_message import TelegramMessage
import os
from garmin import GarminAPI
from formatter_1 import Formatter
from email_message import SendEmail
from mongo_utils import MongoUtils
from boto3_toolkit import Boto3Utils
import pytz
import datetime
import logging

logger = logging.getLogger(__name__)

class Helper:
    def __init__(self):
        ist = pytz.timezone('Asia/Kolkata')
        self.sync_date = datetime.datetime.today().astimezone(ist).strftime('%d/%m/%y')
        self.telegram_docname = f"/tmp/GarminStatistics_{datetime.datetime.today().astimezone(ist).strftime('%d_%m_%y')}.html"
        self.config = Boto3Utils().get_secret(secret_name="GarminSleepStatisticsSecrets")
        self.tg = TelegramMessage()

    def _send_telegram_doc(self, html_body):
        logger.info("Writing HTML body to file for Telegram document")
        with open(self.telegram_docname, 'w') as f:
            f.write(html_body)        
        logger.info("Sending document message via Telegram")
        self.tg.send_document_message(document_file_path=self.telegram_docname, chat_id=self.tg.config["TELEGRAM_CHAT_IDS"]["PAWAN"], caption="Today's Garmin Statistics")        
        logger.info(f"Removing temporary file: {self.telegram_docname}")
        os.remove(self.telegram_docname)
        

    def send_data(self):
        logger.info("Initializing GarminAPI and MongoUtils instances")
        garmin_instance = GarminAPI()
        mongo_instance = MongoUtils()
        logger.info("Fetching data from GarminAPI")
        sleep_data = garmin_instance.getSleepStats()
        body_stats_data = garmin_instance.getYesterdayBodyStats()
        running_data, metadata, activity_id = garmin_instance.getRunningData()
        map_url = garmin_instance.getMapImage(activity_id)
        streak, day_flag = garmin_instance.getRunningStreak()
        metadata.update({"mapUrl": map_url})
        metadata.update({"streak": streak})
        r_html = Formatter().running_html(running_data=running_data, metadata=metadata)
        s_html = Formatter().sleep_html(sleep_data=sleep_data)
        b_html = Formatter().body_stats_html(body_stats_data=body_stats_data)
        if sleep_data and body_stats_data and running_data:
            logger.info("All data fetched successfully. Formatting email body.")
            email_body = Formatter().garminMainEmailFormatter(running_html=r_html, sleep_html=s_html, body_stats_html=b_html, metadata=metadata)
            logger.info("Sending email with Garmin statistics")
            email_message = SendEmail(is_html=True).send_email(body=email_body, subject="Garmin Statistics")
            # self._send_telegram_doc(html_body=email_body)
            logger.info("Updating MongoDB with Garmin status")
            write_in_mongo = mongo_instance.update_record(
                collection_name='garmin_status',
                query={'isUpdated': True},
                update_data={'date': self.sync_date, 'isUpdated': True},
                upsert=True
            )
            logger.info(f"Updated status in MongoDB: {write_in_mongo}")
            logger.info("Inserting sleep data into MongoDB")
            insert_sleep_data_in_mongo = mongo_instance.insert_records(collection_name="garmin_sleep_statistics", data=sleep_data)
            logger.info("Inserting body stats data into MongoDB")
            insert_bodystats_data_in_mongo = mongo_instance.insert_records(collection_name="garmin_body_statistics", data=body_stats_data)
            logger.info("Inserting running data into MongoDB")
            insert_running_data_in_mongo = mongo_instance.insert_records(collection_name="running", data=running_data)
            logger.info(f"Inserted records in MongoDB:\n Sleep Data: {insert_sleep_data_in_mongo}\n Body Statistics: {insert_bodystats_data_in_mongo}\n Running Data: {insert_running_data_in_mongo}")
        else:
            msg = f"No Data Received: Running - {bool(running_data)}, Sleep Statistics - {bool(sleep_data)}, Body Statistics - {bool(body_stats_data)}"
            logger.warning(msg)
            self.tg.send_plain_message(chat_id=self.tg.config["TELEGRAM_CHAT_IDS"]["PAWAN"], text=msg)
