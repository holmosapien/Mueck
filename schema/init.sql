CREATE TABLE account (
    id SERIAL PRIMARY KEY,
    email VARCHAR(64) NOT NULL,
    first_name VARCHAR(64) NOT NULL,
    last_name VARCHAR(64) NOT NULL,
    active BOOLEAN DEFAULT TRUE,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE slack_client (
    id SERIAL PRIMARY KEY,
    api_client_id VARCHAR(64) NOT NULL,
    api_client_secret VARCHAR(64) NOT NULL,
    name VARCHAR(64) NOT NULL,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE slack_oauth_state (
    id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL,
    slack_client_id INTEGER NOT NULL,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    redeemed TIMESTAMP
);

CREATE TABLE slack_integration (
    id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL,
    slack_client_id INTEGER NOT NULL,
    team_id VARCHAR(64) NOT NULL,
    team_name VARCHAR(64) NOT NULL,
    bot_user_id VARCHAR(16) NOT NULL,
    app_id VARCHAR(16) NOT NULL,
    access_token VARCHAR(128) NOT NULL,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE slack_event (
    id SERIAL PRIMARY KEY,
    slack_integration_id INTEGER NOT NULL,
    event JSONB NOT NULL,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed TIMESTAMP
);

CREATE TYPE tensor_art_status AS ENUM ('pending', 'running', 'completed', 'failed');

CREATE TABLE tensor_art_request (
    id SERIAL PRIMARY KEY,
    slack_integration_id INTEGER NOT NULL,
    prompt VARCHAR(1024) NOT NULL,
    job_id VARCHAR(64) NOT NULL,
    job_status tensor_art_status NOT NULL DEFAULT 'pending',
    credits DECIMAL(6, 2) NOT NULL,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE tensor_art_image (
    id SERIAL PRIMARY KEY,
    tensor_art_request_id INTEGER NOT NULL,
    filename VARCHAR(512) NOT NULL,
    width INTEGER NOT NULL,
    height INTEGER NOT NULL,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);