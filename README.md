# Udacitext

## Summary

A small texting application. Runs on Heroku.

Dependencies:

- [flask](http://flask.pocoo.org)
- [gunicorn](http://gunicorn.org)
- [psycopg2](http://initd.org/psycopg/)
- [rq](http://python-rq.org)
- [rq-scheduler](https://github.com/ui/rq-scheduler)
- [twilio](https://www.twilio.com)

See [requirements.txt](requirements.txt) for more details.

## Local Setup

1. Install [Homebrew](http://brew.sh)
2. Install Heroku: `brew install heroku-toolbelt`
3. Install PostgreSQL: `brew install postgres`
4. Install Redis: `brew install redis`
5. Install all of the Python dependencies:
   - `pip install flask`
   - `pip install gunicorn`
   - `pip install psycopg2`
   - `pip install rq`
   - `pip install rq-scheduler`
   - `pip install twilio`
6. Create a [`.env`
   file](https://devcenter.heroku.com/articles/config-vars#local-setup) in the
   project directory which contains the Twilio-related environment variables:
   - `TWILIO_NUMBER`
   - `TWILIO_SID`
   - `TWILIO_TOKEN`
7. Start PostgreSQL: `postgres -D /usr/local/var/postgres`
8. In another terminal window, create your database: `createdb`
9. In that same terminal window, log into PostgreSQL and create all of the
   tables: `psql` and `\i tables.sql`
10. You're done! Feel free to close all of your Terminal windows.

## Local Running

1. In a terminal window, start Redis: `redis-server`
2. In a second terminal window, start PostgreSQL: `postgres -D
   /usr/local/var/postgres`
3. In a third terminal window, log into PostgreSQL so you can modify tables:
   `psql`
4. In a fourth terminal window, navigate to the project directory and start it:
   `heroku local`
5. In a fifth terminal window, navigate to the project directory and import
   the environment variables in your `.env` file, which you'll need to manually
   trigger the scheduling of texts: `export $(cat .env | xargs)`
6. In that same window, manually schedule texts when appropriate: `python
   schedule.py`

## Deploy

If you already have access to the repository or have already installed Heroku,
feel free to skip steps one through three.

1. Clone this repository: `git clone`.
2. Install [Heroku](https://toolbelt.heroku.com). If you don't want to download
   the installer, you can use Homebrew: `brew install heroku-toolbelt`.
3. Configure Heroku: `heroku login`.
4. Add the relevant remote to your repository: `git remote add heroku ...`. The
   repository's path should correspond to your Heroku application's name (i.e.
   https://git.heroku.com/udacitext.git).
5. Push the repository to Heroku: `git push heroku`.

## Configure

Add-ons:

- [Heroku Postgres](https://addons.heroku.com/heroku-postgresql)
- [Heroku Scheduler](https://addons.heroku.com/scheduler)
- [Redis To Go](https://addons.heroku.com/RedisToGo)

Configuration variables:

- `DATABASE_URL`: Comes from Heroku Postgres, defaults to localhost if not
  available
- `HEROKU_POSTGRESQL_BLACK_URL`: Comes from Heroku Postgres, may be of a
  different color (i.e. not black)
- `REDISTOGO_URL`: Comes from Redis To Go, defaults to localhost if not
  available
- `TWILIO_NUMBER`: Phone number to text from
- `TWILIO_SID`: Twilio API SID
- `TWILIO_TOKEN`: Twilio secret token

## Use

The web application accepts texts directed to your endpoint from Twilio. No
configuration should be required except for ensuring that your settings in
Twilio point to the correct URL.

To schedule texts to be sent out, a few tables in PostgreSQL should be
modified:

- `users`: Put all phone numbers in here
- `groups`: Define a group to send students the same messages
- `memberships`: Connect users to groups
- `announcements`: Add announcements to groups

Announcements are assigned to a group and run for a specified amount of time.
The Heroku scheduler calls a script every so often (configurable to be every
ten minutes, every hour, or every day) that inspects these tables, determines
which texts need to be attempted (anyone who hasn't received a valid text yet),
and queues them up for Twilio to send.
