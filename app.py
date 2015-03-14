import os


def run():
    os.system("gunicorn reply:app --log-file=-")


if __name__ == "__main__":
    run()
