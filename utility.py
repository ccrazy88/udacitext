import os
import psycopg2
import urlparse


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


def get_postgres_connection():
    return psycopg2.connect(**POSTGRES_KWARGS)


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
