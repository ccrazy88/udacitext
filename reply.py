from flask import Flask, request
import psycopg2
import os
import twilio.twiml
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


@app.route("/", methods=['GET', 'POST'])
def receive():
    from_body = request.values.get('Body', None)

    messages = []
    if from_body and from_body.strip().upper() in keywords:
        with psycopg2.connect(**POSTGRES_KWARGS) as connection:
            messages = execute_query(
                connection, True,
                """
                SELECT body
                FROM announcements
                WHERE group_id IN (SELECT id FROM groups
                                   WHERE name = 'Broadcast');
                """
            )
        if messages:
            body = ""
            for i, message in enumerate(messages):
                body += "({}/{}) {}\n".format(i + 1, len(messages), message[0])
        else:
            body = ("There aren't any announcements right now. "
                    "Be sure to check back later!")
    else:
        body = ("Welcome to Udacitext.\n"
                "Text NOW to get the latest announcements! "
                "To unsubscribe, text STOP. "
                "(To come back, text START.) "
                "Happy coding!")

    response = twilio.twiml.Response()
    response.message(body)
    return str(response)


def execute_query(connection, return_results, query, *subs):
    cursor = connection.cursor()
    cursor.execute(query, *subs)
    results = cursor.fetchall() if return_results else None
    cursor.close()
    return results


if __name__ == "__main__":
    app.run(debug=True)
