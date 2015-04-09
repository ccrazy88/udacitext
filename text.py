from twilio import TwilioRestException
from twilio.rest import TwilioRestClient

import utility


BLACKLISTED = 21610
FAILED_STATUS = "failed"
CLIENT = TwilioRestClient(utility.TWILIO_SID, utility.TWILIO_TOKEN)


def update_announcements_sent():
    """Update status of announcements sent because texts are asynchronous."""
    with utility.get_postgres_connection() as connection:
        # Messages that haven't had their status finalized are due for an
        # update, if possible.
        messages = utility.execute_query(
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
                message = CLIENT.messages.get(message_sid)
                utility.execute_query(
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
                utility.insert_error(connection, e)


def queue_announcements_to_send():
    """Queue up texts to send."""
    with utility.get_postgres_connection() as connection:
        connection.set_session(autocommit=True)
        messages = utility.execute_query(
            connection, True,
            """
            SELECT phone_number, opted_in, id, body
            FROM announcements, users
            WHERE
                (phone_number, group_id) IN (
                    SELECT phone_number, group_id
                    FROM memberships
                ) AND
                (phone_number, id) NOT IN (
                    SELECT phone_number, announcement_id
                    FROM announcements_sent
                    WHERE status IN ('delivered', 'queued', 'sending', 'sent')
                ) AND
                (phone_number, id) NOT IN (
                    SELECT phone_number, announcement_id
                    FROM announcements_sent
                    GROUP BY phone_number, announcement_id
                    HAVING
                        ABS(EXTRACT(EPOCH FROM MAX(request_timestamp)) -
                            EXTRACT(EPOCH FROM MIN(request_timestamp))) > 3600
                ) AND
                phone_number NOT IN (
                    SELECT phone_number
                    FROM do_not_disturb
                    WHERE
                        EXTRACT(dow from current_date) = dow AND
                        current_time BETWEEN start_time AND end_time
                ) AND
                current_timestamp BETWEEN start_timestamp AND end_timestamp;
            """
        )

        for message in messages:
            phone_number, opted_in, announcement_id, body = message
            try:
                message = CLIENT.messages.create(to=phone_number,
                                                 from_=utility.TWILIO_NUMBER,
                                                 body=body)
                sent_tuple = (phone_number, announcement_id, message.status,
                              None, None, message.sid)
                update_user = True if not opted_in else False
                opted_in_updated = True
            except TwilioRestException as error:
                utility.insert_error(connection, error, phone_number)
                sent_tuple = (phone_number, announcement_id, FAILED_STATUS,
                              error.code, error.msg, None)
                update_user = (True if opted_in and error.code == BLACKLISTED
                               else False)
                opted_in_updated = False

            utility.execute_query(
                connection, False,
                """
                INSERT INTO announcements_sent
                VALUES (DEFAULT, %s, %s, %s, %s, %s, %s, DEFAULT);
                """, sent_tuple
            )
            if update_user:
                utility.execute_query(
                    connection, False,
                    """
                    UPDATE users
                    SET (opted_in, last_updated_timestamp) =
                        (%s, current_timestamp)
                    WHERE phone_number = %s;
                    """, (opted_in_updated, phone_number)
                )


def udacitext():
    update_announcements_sent()
    queue_announcements_to_send()


if __name__ == "__main__":
    udacitext()
