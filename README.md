# FastAPI Lead Intake & AI Lead Qualification System

A Python project that combines a protected FastAPI lead intake endpoint with a separate AI-powered lead qualification workflow.

The project focuses on validating incoming lead data, handling API requests reliably, classifying customer inquiries with structured AI output, and exporting qualification results to CSV.

It was built as a practical project to explore API development, OpenAI integration, data validation, error handling, and automated testing.

## Features

### FastAPI Lead Intake

- REST API built with FastAPI
- Request validation using Pydantic
- Email validation with `EmailStr`
- API-key authentication using `X-API-Key`
- Unique request IDs for tracking
- External API integration for demo company information
- Request timeouts and retry handling
- Controlled HTTP error responses
- Application logging

### AI Lead Qualification

- Single lead qualification using the OpenAI Responses API
- Batch qualification for multiple leads
- Structured AI output using Pydantic models
- Service interest classification
- Urgency classification
- Explanation of classification decisions
- Human review flag for uncertain leads
- Input validation before API requests
- Duplicate lead ID protection
- Verification of AI-returned lead IDs

### CSV Export

- Export batch qualification results to CSV
- UTF-8 BOM encoding for spreadsheet compatibility
- Preservation of Unicode text
- Formula injection mitigation for untrusted text fields

### Reliability and Testing

- OpenAI API timeout and retry configuration
- Handling of authentication, rate-limit, connection, and server errors
- Structured JSON logging
- Request ID and execution-time tracking
- Automated tests using pytest
- Mocked API responses for repeatable testing

---

## Technology Stack

| Technology | Purpose |
|---|---|
| Python 3.14.6 | Main programming language |
| FastAPI | REST API development |
| Pydantic | Data validation and structured output |
| OpenAI Python SDK | AI integration |
| OpenAI Responses API | Lead qualification |
| Requests | External HTTP requests |
| Uvicorn | ASGI application server |
| python-dotenv | Environment configuration |
| pytest | Automated testing |
| httpx2 | HTTP client support for tests and SDK dependencies |

## Project Structure

```text
API/
│
├── main.py
├── test_main.py
│
├── lead_schemas.py
├── qualify_lead.py
├── run_batch_qualification.py
├── export_leads.py
│
├── check_openai_connection.py
│
├── test_lead_schemas.py
├── test_qualify_leads.py
├── test_export_leads.py
│
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## System Overview

The project currently contains two related but separate workflows.

### 1. FastAPI Lead Intake Workflow

```text
Client
  |
  v
POST /leads
  |
  v
Pydantic Validation
  |
  v
API Key Authentication
  |
  v
External Demo API Request
  |
  v
Company Information
  |
  v
Structured API Response
```

The API validates incoming lead information, verifies the client's API key, and performs a read-only lookup against a public demo API.

### 2. AI Lead Qualification Workflow

```text
Customer Lead Messages
          |
          v
    Input Validation
          |
          v
    Batch Preparation
          |
          v
    OpenAI Responses API
          |
          v
  Structured AI Output
          |
          v
    Pydantic Validation
          |
          v
       CSV Export
```

The AI workflow accepts lead messages, classifies them, validates the returned structure, and optionally exports the results to CSV.

The AI qualification workflow is currently implemented separately from the FastAPI `/leads` endpoint.

---

## FastAPI Lead Intake API

The FastAPI application is defined in `main.py`.

### Health Check

**Endpoint**

```http
GET /health
```

Checks whether the API is running.

Example response:

```json
{
  "status": "ok"
}
```

### Create Lead

**Endpoint**

```http
POST /leads
```

This endpoint receives a new lead and requires API-key authentication.

**Required Header**

```http
X-API-Key: your-api-key
```

**Example Request**

```json
{
  "event_id": "evt_001",
  "name": "Rahim Ahmed",
  "email": "rahim@example.com",
  "phone": "01700000000",
  "message": "I need help with workflow automation."
}
```

The `phone` field is optional.

### Lead Data Model

The incoming lead is validated using a Pydantic model.

| Field | Type | Required |
|---|---|---|
| event_id | string | Yes |
| name | string | Yes |
| email | EmailStr | Yes |
| phone | string or null | No |
| message | string | Yes |

### Successful Response

The API returns the received lead, a unique request ID, and the company information obtained from the demo upstream service.

Example structure:

```json
{
  "status": "received",
  "request_id": "generated-uuid",
  "lead": {
    "event_id": "evt_001",
    "name": "Rahim Ahmed",
    "email": "rahim@example.com",
    "phone": "01700000000",
    "message": "I need help with workflow automation."
  },
  "company_info": {
    "id": 1,
    "name": "Demo Company",
    "email": "demo@example.com",
    "phone": "000-000-0000"
  }
}
```

The company information above is illustrative; actual values come from the upstream demo API.

## Authentication and Error Handling

The `/leads` endpoint uses a shared API key supplied through the `X-API-Key` request header.

The server compares the supplied key with the configured `API_KEY`.

| Scenario | HTTP Status |
|---|---:|
| Successful request | 200 |
| Missing required field | 422 |
| Invalid email | 422 |
| Missing API key | 401 |
| Invalid API key | 401 |
| Upstream timeout after retries | 504 |
| Upstream service failure | 502 |

## External API Integration

The FastAPI application uses the following public demo endpoint:

```text
https://jsonplaceholder.typicode.com/users/1
```

This integration demonstrates how an application can retrieve information from an external service.

The request uses:

- A 5-second timeout
- Up to three attempts for selected transient failures
- Controlled error responses after unsuccessful attempts

The upstream request is read-only, so retrying does not create duplicate write operations.

This is demo company information, not a real CRM or customer enrichment integration.

---

## AI-Powered Lead Qualification

The AI functionality is implemented in `qualify_lead.py`.

It uses the OpenAI Responses API with structured output parsing.

### Single Lead Qualification

The `qualify_lead()` function accepts one customer message.

Example:

```python
from qualify_lead import qualify_lead

message = """
I need an AI automation system to manage
my increasing customer inquiries.

This is urgent.
"""

result = qualify_lead(message)

print(result.model_dump_json(indent=2))
```

The function validates the input before making an API request.

Empty messages, whitespace-only messages, and invalid input types are rejected.

### Lead Qualification Schema

The output is validated using the `LeadQualification` Pydantic model.

| Field | Allowed Values / Type |
|---|---|
| service_interest | Literal category |
| urgency | low, medium, high |
| reason | string |
| needs_review | boolean |

**Service Categories**

- `marketing_automation`
- `crm_integration`
- `lead_generation`
- `other`

The `needs_review` field indicates whether the result should be checked by a human.

### Example AI Output

```json
{
  "service_interest": "marketing_automation",
  "urgency": "high",
  "reason": "The lead urgently needs automation to manage increasing customer inquiries.",
  "needs_review": false
}
```

The result is an AI-generated classification and should not be treated as a guaranteed business decision.

---

## Batch Lead Qualification

The `qualify_multiple_leads()` function processes multiple lead messages in one OpenAI Responses API request.

Each input lead must contain:

```json
{
  "lead_id": "L001",
  "message": "I urgently need marketing automation."
}
```

### Batch Validation

Before sending the request, the application checks:

- The input list is not empty.
- Every lead is a dictionary.
- Every lead has a valid, non-empty ID.
- Every message is a non-empty string.
- Duplicate lead IDs are rejected.

The returned AI results are checked to ensure that every input lead ID is represented exactly once.

The batch output uses the `LeadQualificationBatch` Pydantic model.

The batch implementation uses a regular Responses API request containing multiple leads. It is not the separate OpenAI Batch API.

### Run the Batch Demo

```powershell
python run_batch_qualification.py
```

The demonstration uses three sample leads with different service interests and urgency levels.

---

## CSV Export

The `export_leads.py` module exports validated batch results.

**Default output file:**

```text
lead_qualification_results.csv
```

The CSV contains:

| Column | Description |
|---|---|
| lead_id | Original lead identifier |
| service_interest | Classified service |
| urgency | Classified urgency |
| reason | Explanation |
| needs_review | Human review indicator |

The exporter uses UTF-8 with BOM encoding to improve compatibility with spreadsheet applications.

It also applies formula-injection mitigation to untrusted text fields, including lead IDs and qualification reasons.

This is a defensive measure, not a guarantee against every spreadsheet-specific interpretation.

Generated CSV files are excluded from Git through `.gitignore`.

---

## OpenAI API Configuration

The AI qualification module uses the official OpenAI Python SDK.

The client is configured with:

- A 30-second request timeout
- Up to two SDK retries
- Structured output parsing
- Error handling for common API failures

The current model is configured in `qualify_lead.py`.

### OpenAI Error Handling

The application handles:

- API timeout
- Rate-limit errors
- Authentication errors
- Connection errors
- HTTP status errors
- Other API errors

When a request fails, the application logs the error category and execution time without logging the customer message or API key.

## Structured Logging

The AI qualification module uses Python's `logging` module.

It records:

- Request started
- Request completed
- Request failed
- Unique request ID
- Error category
- Execution duration in milliseconds

Example successful event:

```json
{
  "event": "openai_request_completed",
  "request_id": "generated-uuid",
  "status": "success",
  "duration_ms": 1250
}
```

The request ID is generated by the application for internal tracking.

---

## Environment Variables and Security

The project uses environment variables for configuration.

Create a local `.env` file using `.env.example` as a template.

Example:

```env
API_KEY=your-secret-api-key
OPENAI_API_KEY=your-openai-api-key
```

### Security Practices

- API keys are stored in environment variables.
- The real `.env` file is excluded from Git.
- `.venv` is excluded from Git.
- API endpoints validate incoming data.
- The lead intake endpoint requires API-key authentication.
- AI requests use controlled error handling.
- Customer messages and API keys are not included in AI request logs.
- CSV export applies formula-injection mitigation.

Never commit real API keys or other secrets to the repository.

---

## Installation and Setup

### Requirements

- Python 3.14.6 (the version used for project verification)
- pip
- An OpenAI API key for AI features

### 1. Clone the Repository

```bash
git clone https://github.com/Hadicse2007/fastapi-lead-intake-api.git

cd fastapi-lead-intake-api
```

### 2. Create a Virtual Environment

**Windows PowerShell**

```powershell
py -3.14 -m venv .venv

.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks script execution, use a temporary process-level policy:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned

.\.venv\Scripts\Activate.ps1
```

**macOS / Linux**

```bash
python3 -m venv .venv

source .venv/bin/activate
```

### 3. Install Dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy the example file.

**Windows PowerShell**

```powershell
Copy-Item .env.example .env
```

**macOS / Linux**

```bash
cp .env.example .env
```

Open `.env` and provide your own API keys.

Do not share or commit this file.

---

## Running the Application

### Start the FastAPI Server

```bash
python -m uvicorn main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

### Interactive API Documentation

Open:

```text
http://127.0.0.1:8000/docs
```

Use Swagger UI to inspect and test the available endpoints.

### Verify OpenAI API Connection

```bash
python check_openai_connection.py
```

This script checks whether the configured OpenAI API key can be used to make a successful API request.

### Run Single Lead Qualification

```bash
python qualify_lead.py
```

### Run Batch Qualification and CSV Export

```bash
python run_batch_qualification.py
```

The batch demonstration sends a real request to the OpenAI API and creates a CSV output file.

AI requests may incur API usage charges.

---

## Automated Testing

The project uses pytest for automated testing.

Run the complete test suite:

```bash
python -m pytest -v
```

### Test Coverage

| Test File | Coverage |
|---|---|
| `test_main.py` | API endpoints, authentication, validation, upstream failures |
| `test_lead_schemas.py` | Pydantic validation, batch structure, duplicate IDs |
| `test_qualify_leads.py` | Single and batch qualification, input validation, API errors, logging |
| `test_export_leads.py` | CSV creation, data accuracy, Unicode, formula-injection mitigation |

### Latest Verified Test Result

```text
73 passed
```

The complete test suite was also executed successfully in a fresh virtual environment using Python 3.14.6 and the pinned direct dependencies.

External API and OpenAI behaviour is mocked in automated tests. Running the test suite does not require real OpenAI API requests or consume OpenAI API credits.

---

## Current Scope and Limitations

This project is a portfolio and learning implementation.

The following limitations are intentional and should be considered before production use:

- FastAPI lead intake and AI qualification are currently separate workflows.
- The upstream company lookup uses a public demo API.
- Lead information is not stored in a database.
- The batch qualification workflow uses one regular Responses API request.
- CSV files are stored locally.
- Authentication uses a shared API key rather than a full user identity and authorization system.
- There is no background job queue.
- There is no production deployment or CI/CD configuration.
- Production monitoring, rate limiting, and persistent audit storage are not implemented.

## Possible Next Improvements

1. Connect AI qualification directly to the FastAPI lead intake workflow.
2. Add database persistence for incoming leads and qualification results.
3. Integrate a real CRM system.
4. Add background processing for larger workloads.
5. Improve authentication, authorization, and rate limiting.
6. Add deployment and CI/CD automation.
7. Add persistent monitoring and operational reporting.

---

## Project Objective

The objective of this project is to build a practical foundation in Python API development and AI automation.

It combines request validation, API integration, structured AI output, batch processing, CSV export, error handling, and automated testing in one maintainable codebase.

The current implementation is a working prototype that can be extended into a more complete lead management and automation system.