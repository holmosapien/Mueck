# Mueck

## Summary

Mueck is a Slack bot that responds to prompts -- mentions or DMs -- to generate images with Stable Diffusion, and then return them to the channel or user that requested them.

Note: This is a work in progress being built in the open.

## Architecture

There are three main components to Mueck:

1. The Slack bot. This is responsible for registering itself with Slack via OAuth and then exposing an Events API webhook URL that will receive the mentions and DMs. When it receives a request, it is saved to a PostgreSQL database.
2. The Mueck Worker. This runs in a constant loop, reading the queue of incoming image requests from the PostgreSQL database, generating the images, and returning them to Slack.

## Running the Applications

### Dependencies

You need to install PyTorch with CUDA support according to the [documentation at the official PyTorch site](https://pytorch.org/get-started/locally/).

Other dependencies:

```
accelerate
diffusers
fastapi
protobuf
psycopg[binary,pool]
pydantic
transformers
uvicorn
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
export HUGGINGFACE_ACCESS_TOKEN="<token>"
export MUECK_OUTPUT_DIRECTORY="<output_directory>"
export MUECK_DB_HOSTNAME="database.localdomain"
export MUECK_DB_PORT="5432"
export MUECK_DB_USERNAME="mueck"
export MUECK_DB_PASSWORD="<password>"
export MUECK_DB_DATABASE="mueck"

export MUECK_SSL_CERTIFICATE="/etc/openssl/private/mueck.crt"
export MUECK_SSL_PRIVATE_KEY="/etc/openssl/private/mueck.key"
```

### Issuing a Sample Request

```
$ curl -X POST -H "Content-type: application/json" -d '{"prompt": "A pulitzer prize winning photograph of a cat reclining in an Eames chair while smoking a cigarette", "user_id": "UXXX"}' -k https://localhost:11030/api/v1/mueck/request
```

This will return a response with the request ID:

```
{
  "prompt": "A pulitzer prize winning photograph of a cat reclining in an Eames chair while smoking a cigarette",
  "user_id": "UXXX",
  "request_id": 5,
  "processed": false,
  "created": "2024-11-06T18:36:00.698934"
}
```

This request ID can be polled to find out its status:

```
$ curl -s -H "Content-type: application/json" -k https://localhost:11030/api/v1/mueck/request/5 | jq .
{
  "prompt": "A pulitzer prize winning photograph of a cat reclining in an Eames chair while smoking a cigarette",
  "user_id": "UXXX",
  "request_id": 5,
  "processed": true,
  "created": "2024-11-06T18:36:00.698934",
  "width": 512,
  "height": 512,
  "count": 1
}
```

For some reason Stable Diffusion consistently likes to have the smoke billowing from the left ear of the cat.

![A cat smoking a cigarette in an Eames chair.](https://holmosapien.com/a6f1191d90af4b52ac695124a3a6025b.png)