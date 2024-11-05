-- This table contains the raw request.

CREATE TABLE
    request_queue
(
    id SERIAL PRIMARY KEY,
    prompt VARCHAR(1024) NOT NULL,
    processed BOOL NOT NULL DEFAULT false,
    user_id VARCHAR(32) NOT NULL,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- This table contains the parameters after the request
-- has been processed by the initial LLM.

CREATE TABLE
    request_parameter
(
    request_id INT NOT NULL PRIMARY KEY,
    prompt VARCHAR(1024) NOT NULL,
    height INT NOT NULL DEFAULT 512,
    width INT NOT NULL DEFAULT 512,
    count INT NOT NULL DEFAULT 1
);

-- This table contains the filenames that were generated
-- once the request was processed by Stable Diffusion.

CREATE TABLE
    request_filename
(
    request_id INT NOT NULL,
    filename VARCHAR(128) NOT NULL,
    created TIMESTAMP NOT NULL default current_timestamp
);