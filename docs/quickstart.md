# PrefixCTL

## Quickstart

To get a local copy of the repository and change into the directory:
```sh
git clone git@github.com:fullctl/prefixctl
cd prefixctl
```

PrefixCtl is containerized with Docker. First we want to copy the example environment file:
```sh
cp Ctl/dev/example.env Ctl/dev/.env
```
Any of the env variables can be changed, and you should set your own secret key.

Specify a `DJANGO_PORT` variable in the current shell session, this is the port that the Django server will listen on (defaults to `8000`):
```sh
export DJANGO_PORT=8080
```

### Building and starting

You can build / launch the app via:
```sh
Ctl/dev/compose.sh up
```

Open bash in the container:
```sh
Ctl/dev/run.sh /bin/sh
```

Run django commands
```sh
Ctl/dev/run.sh {django_command}
```

## Environment variables

The environment file you copied from `example.env` contains variables for configuring both the Django and Postgres services- if you change the database name, user, or password, you must ensure the values still match between the Django and Postgres settings. The Django database variables are passed directly into the Django application settings so all five `DATABASE_` settings should remain defined.

## Running a standalone local instance of prefixctl.

add `USE_LOCAL_PERMISSIONS=1` to the .env file

Then restart the server
```sh
Ctl/dev/compose.sh restart
```

Then run the following command
```sh
Ctl/dev/run.sh fullctl_local_setup
```

This will setup a superuser and organization.

You can proceed to login at `http://localhost:8080/admin` with the superuser credentials you just created.

After logging in head to `http://localhost:8080` to use PrefixCtl