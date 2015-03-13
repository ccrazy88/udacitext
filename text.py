from datetime import datetime
from twilio import TwilioRestException
from twilio.rest import TwilioRestClient
import os
import psycopg2
import urlparse


# Application constants
BLACKLISTED = 21610
FAILED_STATUS = "failed"

# PostgreSQL constants
urlparse.uses_netloc.append("postgres")
POSTGRES_URL = urlparse.urlparse(os.environ["DATABASE_URL"])
POSTGRES_KWARGS = {
    "database": POSTGRES_URL.path[1:],
    "user": POSTGRES_URL.username,
    "password": POSTGRES_URL.password,
    "host": POSTGRES_URL.hostname,
    "port": POSTGRES_URL.port
}

# Twilio constants
TWILIO_SID = os.environ["TWILIO_SID"]
TWILIO_TOKEN = os.environ["TWILIO_TOKEN"]
TWILIO_NUMBER = os.environ["TWILIO_NUMBER"]


def execute_query(connection, return_results, query, *subs):
    cursor = connection.cursor()
    cursor.execute(query, *subs)
    results = cursor.fetchall() if return_results else None
    cursor.close()
    return results


def insert_error(connection, error, phone_number=None):
    execute_query(
        connection, False,
        """
        INSERT INTO error_log
        VALUES (%s, %s, %s, %s, %s, %s, DEFAULT);
        """,
        (phone_number, error.status, error.uri, error.method, error.code,
         error.msg)
    )


def insert_execution(connection):
    execute_query(connection, False,
                  """INSERT INTO executions VALUES (DEFAULT, DEFAULT)""")


def update_announcements_sent():
    with psycopg2.connect(**POSTGRES_KWARGS) as connection:
        insert_execution(connection)
        messages = execute_query(
            connection, True,
            """
            SELECT message_sid
            FROM announcements_sent
            WHERE status NOT IN ('sent', 'failed', 'delivered', 'undelivered',
                                 'received');
            """
        )
        for message in messages:
            message_sid = message[0]
            try:
                client = TwilioRestClient(TWILIO_SID, TWILIO_TOKEN)
                message = client.messages.get(message_sid)
                execute_query(
                    connection, False,
                    """
                    UPDATE announcements_sent
                    SET (status, error_code, error_message) = (%s, %s, %s)
                    WHERE message_sid = %s;
                    """,
                    (message.status, message.error_code, message.error_message,
                     message_sid)
                )
            except TwilioRestException as e:
                insert_error(connection, e)


def queue_announcements_to_send():
    with psycopg2.connect(**POSTGRES_KWARGS) as connection:
        connection.set_session(autocommit=True)
        insert_execution(connection)
        messages = execute_query(
            connection, True,
            """
            SELECT phone_number, first_name, last_name, opted_in, id, body,
                   image_urls
            FROM announcements, users
            WHERE
                (phone_number, id) NOT IN (
                    SELECT phone_number, announcement_id
                    FROM announcements_sent
                    WHERE status IN ('delivered', 'queued', 'sending', 'sent')
                ) AND
                current_timestamp BETWEEN start_timestamp AND end_timestamp;
            """
        )

        for message in messages:
            (phone_number, first_name, last_name, opted_in, announcement_id,
             body, image_urls) = message
            try:
                client = TwilioRestClient(TWILIO_SID, TWILIO_TOKEN)
                message = client.messages.create(to=phone_number,
                                                 from_=TWILIO_NUMBER,
                                                 body=body)
                sent_tuple = (phone_number, announcement_id, message.status,
                              None, None, message.sid)
                update_user = True if not opted_in else False
                opted_in_updated = True
            except TwilioRestException as error:
                insert_error(connection, error, phone_number)
                sent_tuple = (phone_number, announcement_id, FAILED_STATUS,
                              error.code, error.msg, None)
                update_user = (True if opted_in and error.code == BLACKLISTED
                               else False)
                opted_in_updated = False

            execute_query(
                connection, False,
                """
                INSERT INTO announcements_sent
                VALUES (DEFAULT, %s, %s, %s, %s, %s, %s);
                """, sent_tuple
            )
            if update_user:
                execute_query(
                    connection, False,
                    """
                    UPDATE users
                    SET (opted_in, last_updated_timestamp) = (%s, %s)
                    WHERE phone_number = %s;
                    """, (opted_in_updated, datetime.now(), phone_number)
                )


def udacitext():
    update_announcements_sent()
    queue_announcements_to_send()


if __name__ == "__main__":
    udacitext()
