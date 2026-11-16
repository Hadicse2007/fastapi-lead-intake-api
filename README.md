# FastAPI Lead Intake & AI Lead Qualification

A Python project with a FastAPI-based lead intake API and a separate AI-powered lead qualification workflow.

The API handles incoming lead requests, validates the submitted information, checks API-key authentication and retrieves sample company information from an external service.

The AI workflow takes customer messages, classifies their service interest and urgency, validates the results using Pydantic and exports batch results to CSV.

Both workflows are part of the same project, but they currently run independently.

## What the Project Does

The project covers two main areas of lead management.

### 1. Lead Intake API

- Receives lead information through a REST API.
- Validates incoming data using Pydantic.
- Checks client authentication through an API key.
- Generates a unique request ID for each request.
- Retrieves sample company information from an external API.
- Handles upstream timeouts and service failures.
- Returns structured JSON responses.

### 2. AI Lead Qualification

- Classifies individual customer messages.
- Processes multiple leads in a single OpenAI API request.
- Identifies service interests and urgency levels.
- Provides a reason for each classification.
- Flags uncertain results for human review.
- Validates AI responses against Pydantic schemas.
- Checks that batch results contain the expected lead IDs.

### 3. CSV Export

- Exports batch qualification results.
- Preserves Unicode characters.
- Uses UTF-8 with BOM encoding.
- Applies protection against common spreadsheet formula injection patterns.

### 4. Development and Testing

- Automated tests with pytest.
- Code quality checks with Ruff.
- Dependency consistency checks.
- Python compilation checks.
- GitHub Actions CI on pushes and pull requests.

---

## Technology Stack

| Technology | Purpose |
|---|---|
| Python 3.14.6 | Application development |
| FastAPI | REST API |
| Pydantic | Data validation and structured output |
| OpenAI Python SDK | AI integration |
| OpenAI Responses API | Lead qualification |
| Requests | External HTTP requests |
| Uvicorn | API server |
| python-dotenv | Environment configuration |
| pytest | Automated testing |
| Ruff | Python linting |
| GitHub Actions | Continuous integration |

---

## Project Structure

```text
fastapi-lead-intake-api/
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── main.py
├── check_openai_connection.py
│
├── lead_schemas.py
├── qualify_lead.py
├── run_batch_qualification.py
├── export_leads.py
│
├── test_main.py
├── test_lead_schemas.py
├── test_qualify_leads.py
├── test_export_leads.py
│
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

The virtual environment, local configuration files and generated CSV results are not intended to be committed to the repository.

---

## System Architecture

The application currently has two independent workflows.

### Workflow A: FastAPI Lead Intake

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
       External Demo API
                |
                v
      Company Information
                |
                v
       Structured Response
```

The FastAPI application is responsible for receiving and validating lead information.

After authentication, it requests sample company information from an external service and returns the result to the client.

### Workflow B: AI Lead Qualification

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
          Lead ID Verification
                  |
                  v
             CSV Export
```

The AI workflow is implemented independently of the FastAPI endpoint.

It can qualify a single lead or process multiple leads through the batch function.

The results are validated before being exported.

---

## FastAPI Lead Intake

The API is defined in `main.py`.

### Available Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Checks API availability |
| POST | `/leads` | Receives a new lead |

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

This endpoint can be used to confirm that the application is running.

### Create a Lead

```http
POST /leads
```

The endpoint requires an API key in the request header.

**Request header:**

```http
X-API-Key: your-api-key
```

**Example request:**

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

### Incoming Lead Fields

| Field | Type | Required |
|---|---|---|
| event_id | String | Yes |
| name | String | Yes |
| email | EmailStr | Yes |
| phone | String or null | No |
| message | String | Yes |

The request is validated before the endpoint processes it.

### Response

A successful request returns:

- A processing status.
- A unique request ID.
- The submitted lead information.
- Company information retrieved from the external demo API.

The returned company information is sample data from JSONPlaceholder, not information from a real CRM.

### Authentication and Error Handling

The endpoint compares the supplied `X-API-Key` with the configured server API key.

| Situation | HTTP Status |
|---|---:|
| Successful request | 200 |
| Invalid request data | 422 |
| Invalid or missing API key | 401 |
| Upstream timeout after retries | 504 |
| Upstream service failure | 502 |

### External API Integration

The application uses:

```text
https://jsonplaceholder.typicode.com/users/1
```

This service is used to demonstrate external API communication.

The integration includes:

- A five-second request timeout.
- Up to three attempts for timeouts and server-side failures.
- Controlled error responses when the upstream service remains unavailable.
- Logging with the request ID.

The request is read-only and does not create or modify external records.

---

## AI Lead Qualification

The AI functionality is implemented in `qualify_lead.py`.

It uses the OpenAI Responses API and structured output parsing.

The qualification process identifies four things:

1. The service the customer is interested in.
2. The urgency of the requirement.
3. The reason behind the classification.
4. Whether human review is recommended.

### Supported Service Categories

| Category | Description |
|---|---|
| marketing_automation | Marketing workflow automation |
| crm_integration | CRM and sales system integration |
| lead_generation | Lead generation services |
| other | Other or unclear requirements |

### Urgency Levels

| Level | Description |
|---|---|
| low | No immediate requirement |
| medium | A defined requirement without immediate urgency |
| high | An urgent requirement |

### Structured Output

The qualification result follows the `LeadQualification` Pydantic model.

Example:

```json
{
  "service_interest": "marketing_automation",
  "urgency": "high",
  "reason": "The customer urgently needs automation to manage increasing inquiries.",
  "needs_review": false
}
```

The `needs_review` field indicates whether a human should examine the result.

AI-generated classifications are suggestions and should not be treated as guaranteed business decisions.

### Single Lead Qualification

The `qualify_lead()` function accepts one customer message.

Example:

```python
from qualify_lead import qualify_lead

message = """
I need an AI automation system to manage
our increasing customer inquiries.

This is urgent.
"""

result = qualify_lead(message)

print(result.model_dump_json(indent=2))
```

The function rejects empty messages, whitespace-only messages and invalid input types before making an API request.

---

## Batch Lead Qualification

The `qualify_multiple_leads()` function processes multiple customer messages in one regular OpenAI Responses API request.

Each lead requires a unique ID and a message.

Example input:

```python
leads = [
    {
        "lead_id": "L001",
        "message": "I urgently need marketing automation."
    },
    {
        "lead_id": "L002",
        "message": "We need CRM integration next month."
    }
]
```

### Input Validation

Before sending the request, the application checks:

- The input list is not empty.
- Every item is a dictionary.
- Every lead has a valid ID.
- Every message is a non-empty string.
- Duplicate lead IDs are rejected.

### AI Response Validation

The returned data is parsed using `LeadQualificationBatch`.

The application also verifies that:

- Every input lead ID is returned.
- No lead ID is missing.
- No unexpected lead ID is introduced.
- Duplicate IDs are not accepted.

The batch function uses one regular Responses API request. It does not use the separate OpenAI Batch API.

### Run the Batch Demonstration

```powershell
python run_batch_qualification.py
```

The script processes three sample leads and displays the qualification results.

---

## CSV Export

The `export_leads.py` module handles CSV generation.

The default output filename is:

```text
lead_qualification_results.csv
```

### Exported Fields

| Column | Description |
|---|---|
| lead_id | Original lead identifier |
| service_interest | Classified service |
| urgency | Assigned urgency |
| reason | Explanation of the classification |
| needs_review | Human review indicator |

### Export Handling

The exporter uses:

- Python's CSV module.
- UTF-8 with BOM encoding.
- Formula-injection mitigation for untrusted text values.

The default write mode replaces an existing file with the same name.

Generated CSV files are excluded from Git.

---

## OpenAI Configuration and Error Handling

The OpenAI client is created in `qualify_lead.py`.

The current client configuration includes:

| Setting | Value |
|---|---|
| Request timeout | 30 seconds |
| SDK retries | 2 |
| Response handling | Structured output parsing |

The model is configured in the qualification module.

### Handled API Errors

The application handles common OpenAI API failures:

- Request timeout.
- Rate-limit errors.
- Authentication failures.
- Connection errors.
- HTTP status errors.
- Other API errors.

Errors are converted into controlled application exceptions.

### Logging

The AI module records request events using Python's logging module.

The logs include:

- Request started.
- Request completed.
- Request failed.
- Request ID.
- Error category.
- Execution duration.

Customer messages and API keys are not intentionally included in these AI request log events.

---

## Environment Configuration

The project uses environment variables for sensitive configuration.

Create a local `.env` file using `.env.example` as a template.

Example:

```env
API_KEY=your-secret-api-key
OPENAI_API_KEY=your-openai-api-key
```

`API_KEY` is required by the FastAPI application.

`OPENAI_API_KEY` is required for the AI qualification features.

### Security Practices

- API keys are stored in environment variables.
- `.env` is excluded from Git.
- Virtual environment files are excluded from Git.
- Incoming API data is validated.
- The lead intake endpoint requires API-key authentication.
- AI API errors are handled through controlled exceptions.
- CSV export includes formula-injection mitigation.

Never commit real API keys, passwords or customer information to the repository.

---

## Installation

### Requirements

- Python 3.14.6
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

If PowerShell blocks script execution:

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

**Windows PowerShell**

```powershell
Copy-Item .env.example .env
```

**macOS / Linux**

```bash
cp .env.example .env
```

Open `.env` and add your own API keys.

---

## Running the Application

### Start FastAPI

```bash
python -m uvicorn main:app --reload
```

The local server will be available at:

```text
http://127.0.0.1:8000
```

### Open Swagger UI

```text
http://127.0.0.1:8000/docs
```

Swagger UI provides an interactive interface for testing the available API endpoints.

For the protected `/leads` endpoint, provide the `X-API-Key` header.

### Check OpenAI API Connection

```bash
python check_openai_connection.py
```

This script checks the configured OpenAI API connection.

### Run Single Lead Qualification

```bash
python qualify_lead.py
```

### Run Batch Qualification and Export

```bash
python run_batch_qualification.py
```

This script sends the sample leads to OpenAI, displays the qualification results and generates the CSV file.

**Note:** The AI scripts make real API requests. OpenAI usage charges may apply.

---

## Automated Testing

The project uses pytest to test the main application components.

Run all tests:

```bash
python -m pytest -v
```

### Test Modules

| File | Main Test Areas |
|---|---|
| `test_main.py` | Health check, lead intake, authentication, validation and upstream failures |
| `test_lead_schemas.py` | Qualification schemas, batch validation and duplicate IDs |
| `test_qualify_leads.py` | Single and batch qualification, API errors and logging |
| `test_export_leads.py` | CSV creation, data accuracy, Unicode and formula-injection mitigation |

### Latest Verified Test Result

```text
73 passed
```

The test suite uses mocked API responses for external service and OpenAI interactions. Running the automated tests does not require live OpenAI API requests.

---

## Code Quality and Continuous Integration

The repository uses Ruff and GitHub Actions to maintain code quality.

### Run Ruff Locally

```bash
python -m ruff check .
```

### Check Dependencies

```bash
python -m pip check
```

### Compile Python Files

```bash
python -m compileall -q .
```

### GitHub Actions

The CI workflow is located at:

```text
.github/workflows/ci.yml
```

It runs on:

- Push events.
- Pull requests targeting `main`.

The workflow performs the following checks:

1. Checks out the repository.
2. Sets up Python 3.14.6.
3. Installs project dependencies.
4. Checks dependency consistency.
5. Compiles Python files.
6. Runs Ruff checks.
7. Runs the complete pytest suite.

The workflow helps identify code and test failures before changes are merged into the main branch.

---

## Current Scope and Limitations

This project is a working development and portfolio implementation. It is not yet a complete production lead management platform.

Current limitations include:

- FastAPI lead intake and AI qualification run as separate workflows.
- Company information comes from a public demo API.
- Lead records are not stored in a database.
- Batch qualification uses one regular OpenAI Responses API request.
- CSV results are stored locally.
- Authentication uses a shared API key.
- There is no background task queue.
- There is no integrated CRM.
- Production deployment and monitoring have not been implemented.
- Rate limiting and a full user authorization system are not included.

These are areas that can be addressed as the project develops.

---

## Future Development

Possible improvements include:

1. Connecting AI qualification directly to the FastAPI lead intake endpoint.
2. Adding