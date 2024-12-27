# Mueck

## Summary

Mueck is a Slack bot that responds to prompts -- mentions or DMs -- to generate TensorArt jobs, and then return the resulting images to the channel or user that requested them.

Note: This is a work in progress being built in the open.

## Architecture

There are two main components to Mueck:

1. The Slack bot. This is responsible for registering itself with Slack via OAuth and then exposing an Events API webhook URL that will receive mentions. When it receives a request, it is saved to a PostgreSQL database.
2. The Mueck Worker. This runs in a constant loop, reading the queue of incoming image requests from the PostgreSQL database, generating the images and returning them to Slack.

## Running the Applications

### Dependencies

```
$ python3.13 -m venv venv
$ source venv/bin/activate
[venv] $ pip install -r requirements.txt
```

### Creating the Database

```
CREATE DATABASE mueck;
CREATE USER mueck WITH PASSWORD '<password>';
GRANT ALL PRIVILEGES ON DATABASE mueck TO mueck;
ALTER DATABASE mueck OWNER TO mueck;
```

Now you can connect to the `mueck` database and create the tables in `schema/init.sql`.

### Environment Variables

```
export MUECK_LISTENER_HOSTNAME='mueck.domain'
export MUECK_DOWNLOAD_PATH="<output_directory>"

export TENSORART_API_KEY='<api key>'

export MUECK_DB_HOSTNAME='database.localdomain'
export MUECK_DB_PORT='5432'
export MUECK_DB_USERNAME='mueck'
export MUECK_DB_PASSWORD='<password>'
export MUECK_DB_DATABASE='mueck'

# If you want TLS for your PostgreSQL connection:

export MUECK_DB_CA='/etc/openssl/private/ca.crt'
export MUECK_DB_CERTIFICATE='/etc/openssl/private/client.crt'
export MUECK_DB_PRIVATE_KEY='/etc/openssl/private/client.key'

# If you want FastAPI to listen on https:

export MUECK_TLS_CERTIFICATE='/etc/openssl/private/mueck.crt'
export MUECK_TLS_PRIVATE_KEY='/etc/openssl/private/mueck.key'
```

### Running the Listener and Worker

```
[venv] $ python3 mueck.py
[venv] $ python3 mueckworker.py
```

### Setting up the Slack Application

Edit `appManifest.json` according to your environment, and use it to create your Slack application at https://api.slack.com/apps.

Once you have your client ID and client secret, you must add them to the database:

```
mueck=> INSERT INTO account (email, first_name, last_name) VALUES ('email@domain', 'First', 'Last') RETURNING id;
 id
----
  1
(1 row)

INSERT 0 1
mueck=> INSERT INTO slack_client (api_client_id, api_client_secret, name) VALUES ('client_id', 'client_secret', 'team_name') RETURNING id;
 id
----
  1
(1 row)
```

Now you can use the `/api/v1/mueck/slack-redirect-link` endpoint to get a link to the URL to install your application in your Slack workspace.

```
$ curl `http://localhost:12030/api/v1/mueck/slack-redirect-link?account_id=1&slack_client_id=1`
```

Visit the link in your browser, approve the requested permissions, and now you can invite @Mueck into your channels for chatting.