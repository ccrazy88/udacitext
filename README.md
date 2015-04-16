# Udacitext

## Summary

Runs on Heroku.

Dependencies:

- [gunicorn](http://gunicorn.org)
- [psycopg](http://initd.org/psycopg/)
- [rq](http://python-rq.org)
- [rq-scheduler](https://github.com/ui/rq-scheduler)
- [twilio](https://www.twilio.com)

See [requirements.txt](requirements.txt) for more details.

## Installation

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

## Configuration

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

Running locally:

- Install [Homebrew](http://brew.sh)
- Install PostgreSQL: `brew install postgres`
- Install Redis: `brew install redis`
- Set the environment variables for Twilio phone number, SID, and secret token

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
