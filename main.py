#create fast api, lead model, and health check endpoint

from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel, EmailStr
from dotenv import load_dotenv
import os
import logging
import json
import uuid
import requests


# .env file load করে
load_dotenv()


# .env থেকে API_KEY নেয়
APIkey = os.getenv("API_KEY")


# API key না থাকলে application startup বন্ধ করে
if not APIkey:
    raise ValueError("API_KEY not found in environment variables")


# Application-এর logging configuration সেট করে
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# এই module-এর জন্য logger তৈরি করে
logger = logging.getLogger(__name__)


# FastAPI application তৈরি করে
app = FastAPI()


# Incoming lead-এর data structure এবং validation rules নির্ধারণ করে
class Lead(BaseModel):
    event_id: str
    name: str
    email: EmailStr
    phone: str | None = None
    message: str


# External demo API থেকে mock company information আনে
def get_mock_company_info(request_id):

    # যে external/upstream API-তে request পাঠাব
    url = "https://jsonplaceholder.typicode.com/users/1"

    # সর্বোচ্চ 3 বার চেষ্টা করার অনুমতি দেয়
    max_retries = 3


    # Attempt 1, 2, 3 চালায়
    for attempt in range(1, max_retries + 1):

        try:

            # External API call করে এবং সর্বোচ্চ 5 seconds অপেক্ষা করে
            response = requests.get(url, timeout=5)


            # Upstream server 500+ error দিলে retry logic চালায়
            if response.status_code >= 500:

                logger.warning(json.dumps({
                    "request_id": request_id,
                    "attempt": attempt,
                    "status": "upstream_error",
                    "upstream_status": response.status_code
                }))


                # শেষ attempt-ও fail করলে controlled 502 error দেয়
                if attempt == max_retries:
                    raise HTTPException(
                        status_code=502,
                        detail={
                            "request_id": request_id,
                            "message": "Upstream service failed"
                        }
                    )


                # পরবর্তী retry attempt-এ চলে যায়
                continue


            # 4xx-এর মতো অন্য HTTP error থাকলে exception তৈরি করে
            response.raise_for_status()


            # Successful JSON response Python dictionary-তে convert করে
            data = response.json()


            # Demo response থেকে প্রয়োজনীয় information নেয়
            company_info = {
                "id": data.get("id"),
                "name": data.get("name"),
                "email": data.get("email"),
                "phone": data.get("phone")
            }


            # Successful upstream call log করে
            logger.info(json.dumps({
                "request_id": request_id,
                "status": "success",
                "message": "Successfully fetched mock company info"
            }))


            # পাওয়া information caller-এর কাছে ফেরত দেয়
            return company_info


        # External API সময়মতো response না দিলে timeout ধরে
        except requests.exceptions.Timeout:

            logger.warning(json.dumps({
                "request_id": request_id,
                "attempt": attempt,
                "status": "upstream_timeout"
            }))


            # তিনবারই timeout হলে client-কে controlled 504 দেয়
            if attempt == max_retries:
                raise HTTPException(
                    status_code=504,
                    detail={
                        "request_id": request_id,
                        "message": "Upstream service timed out"
                    }
                )


        # Timeout ছাড়া requests library-এর অন্য error handle করে
        except requests.exceptions.RequestException as e:

            logger.error(json.dumps({
                "request_id": request_id,
                "status": "upstream_request_error",
                "message": str(e)
            }))


            # Upstream communication failure হিসেবে 502 পাঠায়
            raise HTTPException(
                status_code=502,
                detail={
                    "request_id": request_id,
                    "message": "Upstream service error"
                }
            )


# API/server alive আছে কিনা check করার endpoint
@app.get("/health")
def health_check():

    logger.info("Health check requested")

    return {
        "status": "ok"
    }


# নতুন lead receive করার protected endpoint
@app.post("/leads")
def create_lead(
    lead: Lead,
    api_key: str | None = Header(
        default=None,
        alias="X-API-Key"
    )
):

    # এই particular request-এর জন্য unique tracking ID তৈরি করে
    request_id = str(uuid.uuid4())


    # Client-এর API key এবং server-এর API key compare করে
    if api_key != APIkey:

        # Unauthorized attempt log করে
        logger.warning(json.dumps({
            "request_id": request_id,
            "status": "unauthorized",
            "message": "Invalid API Key"
        }))


        # Wrong/missing API key হলে request বন্ধ করে 401 দেয়
        raise HTTPException(
            status_code=401,
            detail={
                "request_id": request_id,
                "message": "Invalid API Key"
            }
        )


    # Authentication successful হওয়ার পর external API call করে
    company_info = get_mock_company_info(request_id)


    # Lead successfully process হওয়ার ঘটনা log করে
    logger.info(json.dumps({
        "request_id": request_id,
        "status": "received",
        "event_id": lead.event_id
    }))


    # Final successful response client-কে পাঠায়
    return {
        "status": "received",
        "request_id": request_id,
        "lead": lead,
        "company_info": company_info
    }