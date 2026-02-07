# Centralized Logging Service

A lightweight centralized logging service built with FastAPI and Supabase, allowing you to create, query, and manage logs from multiple services and environments.

## Features

- **Create logs**: Ingest log data with flexible fields including service, environment, level, message, trace ID, and arbitrary metadata.
- **Query logs**: Retrieve logs based on service name, log level, and specify limits for the number of results.
- **Retrieve individual logs**: Fetch specific log entries using their unique ID.
- **Delete logs**: Remove log entries, useful for data retention policies and cleanup.
- **Health check**: A simple endpoint to monitor the service's operational status.

## Table of Contents

- [Installation](#installation)
- [Configuration](#configuration)
- [API Endpoints](#api-endpoints)
- [Example Requests](#example-requests)
- [Response Models](#response-models)

## Installation

To get started with the Centralized Logging Service, follow these steps:

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd <repo-directory>
    ```

2.  **Install dependencies:**
    This project uses `pip` for dependency management. Install the required packages using the `requirements.txt` file:
    ```bash
    pip install -r requirements.txt
    ```
    (Note: The existing `README.md` specified `pip install fastapi uvicorn python-dotenv supabase`. Using `requirements.txt` is generally better practice if it exists, otherwise, the explicit command is fine. I'll assume `requirements.txt` is the intended way based on its presence in the directory listing).

3.  **Run the server:**
    Use `uvicorn` to start the FastAPI application. The `--reload` flag is useful for development as it restarts the server on code changes.
    ```bash
    uvicorn main:app --reload
    ```
    The server will be accessible at `http://127.0.0.1:8000` by default.

## Configuration

The application requires environment variables for connecting to your Supabase instance. Create a `.env` file in the root directory of the project with the following content:

```dotenv
SUPABASE_URL=<your-supabase-url>
SUPABASE_KEY=<your-supabase-key>
```

**Supabase Table Schema:**
Ensure your Supabase database has a table named `logs` with the following columns. The `id` and `created_at` fields are typically handled automatically by Supabase when `insert`ing data.

| Column Name | Type      | Description                            |
| :---------- | :-------- | :------------------------------------- |
| `id`        | `uuid`    | Unique identifier for the log entry    |
| `service`   | `text`    | Name of the service generating the log |
| `environment` | `text`    | Deployment environment (e.g., `production`, `development`) |
| `level`     | `text`    | Log severity level (e.g., `INFO`, `WARN`, `ERROR`, `DEBUG`) |
| `log_message` | `text`    | The main log message                   |
| `trace_id`  | `text`    | Optional: Identifier for tracing requests across services |
| `metadata`  | `jsonb`   | Optional: Additional structured context or data in JSON format |
| `created_at` | `timestamp with time zone` | Timestamp of log creation, defaults to `now()` |

## API Endpoints

### 1. Create a Log

-   **Path:** `POST /v1/logs`
-   **Description:** Ingests a new log entry into the system.
-   **Request Body (`application/json`):**
    | Field         | Type      | Description                            | Example             |
    | :------------ | :-------- | :------------------------------------- | :------------------ |
    | `service`     | `string`  | Name of the service (required)         | `"payment-api"`     |
    | `environment` | `string`  | Environment (required)                 | `"production"`      |
    | `level`       | `string`  | Log level (required, e.g., `ERROR`)    | `"ERROR"`           |
    | `log_message` | `string`  | The log message (required)             | `"Payment gateway timeout"` |
    | `trace_id`    | `string`  | Optional trace identifier              | `"req-123"`         |
    | `metadata`    | `object`  | Optional additional contextual info    | `{"order_id": 9981}` |
-   **Response:** `LogResponse` (200 OK)

### 2. List Logs

-   **Path:** `GET /v1/logs`
-   **Description:** Retrieves a list of log entries, with optional filtering and limiting.
-   **Query Parameters (Optional):**
    | Parameter | Type      | Description                              | Example             |
    | :-------- | :-------- | :--------------------------------------- | :------------------ |
    | `service` | `string`  | Filter logs by the name of the service   | `?service=payment-api` |
    | `level`   | `string`  | Filter logs by severity level            | `?level=ERROR`      |
    | `limit`   | `integer` | Number of logs to return (max 500, default 100) | `?limit=50`         |
-   **Response:** `List[LogResponse]` (200 OK)

### 3. Get Log by ID

-   **Path:** `GET /v1/logs/{log_id}`
-   **Description:** Retrieves a single log entry by its unique ID.
-   **Path Parameters:**
    | Parameter | Type     | Description             | Example                          |
    | :-------- | :------- | :---------------------- | :------------------------------- |
    | `log_id`  | `string` | The unique ID of the log | `a1b2c3d4-e5f6-7890-1234-567890abcdef` |
-   **Response:** `LogResponse` (200 OK)
-   **Error:** 404 Not Found if the log ID does not exist.

### 4. Delete Log

-   **Path:** `DELETE /v1/logs/{log_id}`
-   **Description:** Deletes a log entry from the system based on its ID.
-   **Path Parameters:**
    | Parameter | Type     | Description             | Example                          |
    | :-------- | :------- | :---------------------- | :------------------------------- |
    | `log_id`  | `string` | The unique ID of the log | `a1b2c3d4-e5f6-7890-1234-567890abcdef` |
-   **Response:**
    ```json
    {
      "status": "deleted"
    }
    ```
    (200 OK)

### 5. Health Check

-   **Path:** `GET /health`
-   **Description:** Provides a simple health check to indicate if the service is running.
-   **Response:**
    ```json
    {
      "status": "ok"
    }
    ```
    (200 OK)

## Example Requests

Here are some `curl` examples to interact with the API:

### Create Log

```bash
curl -X POST http://127.0.0.1:8000/v1/logs \
-H "Content-Type: application/json" \
-d '{
  "service": "payment-api",
  "environment": "prod",
  "level": "ERROR",
  "log_message": "Payment gateway timeout",
  "trace_id": "req-123",
  "metadata": {
    "order_id": 9981,
    "latency_ms": 2500
  }
}'
```

### List Logs

```bash
curl "http://127.0.0.1:8000/v1/logs?service=payment-api&level=ERROR&limit=50"
```

### Get Log by ID

Replace `<log_id>` with an actual log ID from your Supabase table.

```bash
curl "http://127.0.0.1:8000/v1/logs/<log_id>"
```

### Delete Log

Replace `<log_id>` with the ID of the log you wish to delete.

```bash
curl -X DELETE "http://127.0.0.1:8000/v1/logs/<log_id>"
```

## Response Models

### `LogCreate` Example

This represents the structure of the data sent when creating a new log.

```json
{
  "service": "chat-api",
  "environment": "production",
  "level": "ERROR",
  "log_message": "Some error occurred",
  "trace_id": "req-123",
  "metadata": { "user_id": "abc-123", "component": "authentication" }
}
```

### `LogResponse` Example

This includes the `id` and `created_at` fields generated by the database, in addition to the `LogCreate` fields.

```json
{
  "id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
  "created_at": "2026-02-07T12:00:00.000000+00:00",
  "service": "chat-api",
  "environment": "production",
  "level": "ERROR",
  "log_message": "Some error occurred",
  "trace_id": "req-123",
  "metadata": { "user_id": "abc-123", "component": "authentication" }
}
```