from flask import Flask, request
import twilio.twiml

import utility


app = Flask(__name__)
KEYWORDS = ["ANNOUNCEMENT", "ANNOUNCEMENTS", "LATEST", "NOW"]


@app.route("/", methods=['GET', 'POST'])
def receive():
    """Respond to texts sent via a Twilio endpoint.

    Handle texts sent by sending the user a welcome message or, if appropriate,
    a series of announcements."""
    messages = []

    # If the message received is one of the keywords, send the person some
    # broadcasts. Otherwise, send them a welcome message.
    from_body = request.values.get('Body', None)
    if from_body and from_body.strip().upper() in KEYWORDS:
        with utility.get_postgres_connection() as connection:
            messages = utility.execute_query(
                connection, True,
                """
                SELECT body
                FROM announcements
                WHERE group_id IN (SELECT id FROM groups
                                   WHERE UPPER(name) = 'BROADCAST');
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


if __name__ == "__main__":
    app.run(debug=True)
