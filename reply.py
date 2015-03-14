from flask import Flask, request
from twilio import TwilioRestException
from twilio.rest import TwilioRestClient
import psycopg2
import os
import urlparse


# Application constants
app = Flask(__name__)
keywords = ["ANNOUNCEMENT", "ANNOUNCEMENTS", "LATEST", "NOW"]

# PostgreSQL constants
urlparse.uses_netloc.append("postgres")
postgres_url = os.getenv("DATABASE_URL", 'postgres://localhost:5432')
url = urlparse.urlparse(postgres_url)
POSTGRES_KWARGS = {
    "database": url.path[1:],
    "user": url.username,
    "password": url.password,
    "host": url.hostname,
    "port": url.port
}

# Twilio constants
TWILIO_SID = os.environ["TWILIO_SID"]
TWILIO_TOKEN = os.environ["TWILIO_TOKEN"]
TWILIO_NUMBER = os.environ["TWILIO_NUMBER"]


@app.route("/", methods=['GET', 'POST'])
def receive():
    phone_number = request.values.get('From', None)
    from_body = request.values.get('Body', None)

    if from_body and from_body.strip().upper() in keywords:
        with psycopg2.connect(**POSTGRES_KWARGS) as connection:
            messages = execute_query(
                connection, True,
                """
                SELECT body
                FROM announcements
                WHERE current_timestamp BETWEEN start_timestamp AND
                                                end_timestamp;
                """
            )
            for message in messages:
                body = message[0]
                try:
                    client = TwilioRestClient(TWILIO_SID, TWILIO_TOKEN)
                    message = client.messages.create(to=phone_number,
                                                     from_=TWILIO_NUMBER,
                                                     body=body)
                except TwilioRestException as error:
                    insert_error(connection, error, phone_number)
    else:
        body = ("Welcome to Udacitext.\n"
                "Send NOW to get the latest announcements! "
                "To unsubscribe, send STOP. "
                "(To come back, send START.) "
                "Happy coding!")
        try:
            client = TwilioRestClient(TWILIO_SID, TWILIO_TOKEN)
            message = client.messages.create(to=phone_number,
                                             from_=TWILIO_NUMBER,
                                             body=body)
        except TwilioRestException as error:
            with psycopg2.connect(**POSTGRES_KWARGS) as connection:
                insert_error(connection, error, phone_number)

    return "Udacitext!"


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


if __name__ == "__main__":
    app.run(debug=True)
