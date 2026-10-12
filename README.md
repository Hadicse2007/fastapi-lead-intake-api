# FastAPI Lead Intake & Validation API

A FastAPI-based lead intake API designed with validation, authentication, external API integration, failure handling, structured logging, and automated testing.

The service accepts lead data, validates incoming requests, protects the main endpoint with API-key authentication, performs a read-only external API lookup, and handles upstream failures such as timeouts and server errors.

---

## Features

- REST API built with FastAPI
- Lead validation using Pydantic
- Email validation with `EmailStr`
- API-key authentication using `X-API-Key`
- Unique request IDs for request tracing
- External API integration
- Request timeout handling
- Limited retries for transient failures
- Controlled HTTP error responses
- Structured application logging
- Environment-variable based configuration
- Automated testing with `pytest`
- Mocked upstream API failures during tests

---

## Tech Stack

- Python
- FastAPI
- Pydantic
- Requests
- python-dotenv
- Pytest
- Uvicorn

---

## Project Structure

```text
API/
│
├── main.py
├── test_main.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## API Endpoints

### Health Check

```http
GET /health
```

Example response:

```json
{
  "status": "ok"
}
```

---

### Create Lead

```http
POST /leads
```

Required header:

```text
X-API-Key: your-api-key
```

Example request body:

```json
{
  "event_id": "evt_001",
  "name": "Rahim Ahmed",
  "email": "rahim@example.com",
  "phone": "01700000000",
  "message": "I need help with workflow automation."
}
```

`phone` is optional.

---

## Validation and Error Handling

Incoming lead data is validated using Pydantic.

| Scenario | Status Code |
|---|---:|
| Valid request | `200` |
| Missing required field | `422` |
| Invalid email | `422` |
| Missing API key | `401` |
| Wrong API key | `401` |
| Upstream timeout after retries | `504` |
| Upstream server failure after retries | `502` |

---

## External API and Retry Handling

The service performs a read-only lookup against a public demo API to demonstrate upstream API integration and failure handling.

The request uses a timeout:

```python
requests.get(url, timeout=5)
```

Selected transient failures, including timeouts and upstream `5xx` errors, are retried up to three times before a controlled error response is returned.

Because the upstream operation is read-only, retrying does not create duplicate side effects.

---

## Environment Variables

Create a local `.env` file:

```env
API_KEY=your-secret-api-key
```

A safe template is included in:

```text
.env.example
```

Example:

```env
API_KEY=your-api-key-here
```

The real `.env` file is excluded from Git and should never be committed.

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/Hadicse2007/fastapi-lead-intake-api.git
cd fastapi-lead-intake-api
```

### 2. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file based on `.env.example`:

```env
API_KEY=your-secret-api-key
```

---

## Run the API

Start the development server:

```bash
python -m uvicorn main:app --reload
```

Open the interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

---

## Automated Testing

Run the test suite with:

```bash
python -m pytest -v
```

The current test suite covers:

- Health endpoint
- Valid lead submission
- Missing required field
- Invalid email
- Missing API key
- Wrong API key
- Upstream timeout with retries
- Upstream `500` failure with retries

Current test result:

```text
8 passed
```

External API behaviour is mocked during tests, so the test suite does not depend on the real upstream service being available.

---

## Engineering Highlights

- Request validation with Pydantic
- API-key protected endpoint
- Request-level trace IDs
- External API integration with timeout protection
- Retry handling for transient upstream failures
- Structured logging for troubleshooting
- Controlled authentication and validation errors
- Automated testing of both success and failure paths
- Mocked upstream failures for repeatable tests

---

## Scope and Limitations

This implementation focuses on API intake, validation, authentication, upstream reliability, logging, and automated testing.

The following capabilities are intentionally outside the current scope:

- Database persistence
- Duplicate event protection
- OAuth
- CRM integration
- Deployment
- CI/CD
- Persistent processing state