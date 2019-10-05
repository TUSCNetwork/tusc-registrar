create table tusc_account_registrations (
    id                      SERIAL,
    tusc_account_name       text not null,
    tusc_public_key         TEXT NOT NULL DEFAULT '',
    created_at              timestamp without time zone default (now() at time zone 'utc'),
    primary key (id, tusc_account_name)
);