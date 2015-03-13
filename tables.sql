-- Preserve history too?

CREATE TABLE users (
    phone_number text PRIMARY KEY,
    first_name text NOT NULL,
    last_name text,
    opted_in boolean NOT NULL,
    last_updated_timestamp timestamp with time zone DEFAULT current_timestamp
);

CREATE TABLE do_not_disturb (
    phone_number text NOT NULL REFERENCES users ON DELETE RESTRICT,
    dow integer NOT NULL CHECK (dow >= 0 AND dow < 7),
    start_time time with time zone NOT NULL,
    end_time time with time zone NOT NULL CHECK (end_time > start_time)
);

CREATE TABLE announcements (
    id serial PRIMARY KEY,
    body text NOT NULL,
    image_urls text[],
    start_timestamp timestamp with time zone NOT NULL,
    end_timestamp timestamp with time zone NOT NULL
                  CHECK (end_timestamp > start_timestamp)
);

CREATE TYPE status AS ENUM (
    -- Twilio's message statuses.
    'queued',
    'sending',
    'sent',
    'failed',
    'delivered',
    'undelivered',
    'receiving',
    'received'
);

CREATE TABLE announcements_sent (
    id serial PRIMARY KEY,
    phone_number text NOT NULL REFERENCES users ON DELETE RESTRICT,
    announcement_id integer NOT NULL REFERENCES announcements (id)
                    ON DELETE RESTRICT,
    status status NOT NULL,
    error_code text,
    error_message text,
    message_sid text,
    request_timestamp timestamp with time zone DEFAULT current_timestamp
);

CREATE TABLE error_log (
    phone_number text REFERENCES users ON DELETE RESTRICT,
    status integer,
    uri text,
    method text,
    error_code text,
    error_message text,
    create_timestamp timestamp with time zone DEFAULT current_timestamp
);

CREATE TABLE executions (
    id serial PRIMARY KEY,
    create_timestamp timestamp with time zone DEFAULT current_timestamp
);
