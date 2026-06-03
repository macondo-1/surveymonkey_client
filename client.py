import requests
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
_ROOT = Path(__file__).resolve().parent
load_dotenv(_ROOT / ".env")
bearer_token = os.environ.get("SISINTL11_BEARER_TOKEN")


RATELIMIT_THRESHOLD = 50


class SurveyMonkeyClient:
    BASE_URL = "https://api.surveymonkey.com/v3"

    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
        self.ratelimit_remaining = None
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"bearer {bearer_token}",
            "Content-Type": "application/json",
        })
        self._request("GET", "surveys?per_page=1")

    def _request(self, method, endpoint, **kwargs):
        if self.ratelimit_remaining is not None and int(self.ratelimit_remaining) <= RATELIMIT_THRESHOLD:
            raise RuntimeError(f"Daily rate limit nearly exhausted: {self.ratelimit_remaining} remaining")
        response = self.session.request(method, f"{self.base_url}/{endpoint}", **kwargs)
        self.ratelimit_remaining = response.headers.get('X-Ratelimit-App-Global-Day-Remaining')
        return response

    def get(self, endpoint):
        return self._request("GET", endpoint)

    def post(self, endpoint, data):
        return self._request("POST", endpoint, json=data)

    def survey_details(self, survey_id):
        return self.get(f"surveys/{survey_id}/details")


def main():
    sm_client = SurveyMonkeyClient()
        # Example: Get details of a specific survey (Replace '123456789' with an actual survey ID)
    survey_id = "130579674"
    try:
        details_response = sm_client.survey_details(survey_id)
        if details_response.status_code == 200:
            print(details_response.json())
        else:
            print(f"Failed to get survey details: {details_response.status_code} - {details_response.text}")
    except RuntimeError as e:
        print(str(e))

    
if __name__ == "__main__":
    main()