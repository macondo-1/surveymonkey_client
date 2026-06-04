import requests
import os
from pathlib import Path
from dotenv import load_dotenv
import json
from functools import wraps

# Load environment variables from .env file
_ROOT = Path(__file__).resolve().parent
load_dotenv(_ROOT / ".env")


RATELIMIT_THRESHOLD = 50


class SurveyMonkeyClient:
    BASE_URL = "https://api.surveymonkey.com/v3"

    def __init__(self, base_url=BASE_URL, account_id="SISINTL11"):
        self.base_url = base_url
        self.account_id = account_id
        self.ratelimit_remaining = None
        self.bearer_token = os.environ.get(f"{self.account_id}_BEARER_TOKEN")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"bearer {self.bearer_token}",
            "Content-Type": "application/json",
        })
        self._request("GET", "surveys?per_page=1")

    def _request(self, method, endpoint, **kwargs):
        if self.ratelimit_remaining is not None and int(self.ratelimit_remaining) <= RATELIMIT_THRESHOLD:
            raise RuntimeError(f"Daily rate limit nearly exhausted: {self.ratelimit_remaining} remaining")
        
        if endpoint.startswith("https"):
            url = endpoint
        else:
            url = f"{self.base_url}/{endpoint}"

        response = self.session.request(method, url, **kwargs)
        response.raise_for_status()
        self.ratelimit_remaining = response.headers.get('X-Ratelimit-App-Global-Day-Remaining')
        return response



    def post(self, endpoint, data):
        return self._request("POST", endpoint, json=data)

    def get_survey_details(self, survey_id):
        return self.get(f"surveys/{survey_id}/details")

    def get_collector_details(self, collector_id):
        return self.get(f"collectors/{collector_id}")

    def get(self, endpoint) -> requests.Response:
        return self._request("GET", endpoint)

    def paginate(func) -> generator:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            response = func(self, *args, **kwargs)
            while True:
                body = response.json()
                yield from body.get("data", [])
                next_link = body.get("links", {}).get("next")
                if not next_link:
                    break
                response = self.session.get(next_link)
        return wrapper

    get_paginated = paginate(get)

    def get_survey_answers(self, survey_id, per_page=100) -> generator:
        return self.get_paginated(f"surveys/{survey_id}/responses/bulk?per_page={per_page}")

    def get_survey_collectors(self, survey_id, per_page=100) -> generator:
        return self.get_paginated(f"surveys/{survey_id}/collectors?per_page={per_page}")

    def get_account_surveys(self, per_page=100) -> generator:
        return self.get_paginated(f"surveys?per_page={per_page}")



def main():
    sm_client = SurveyMonkeyClient(account_id="SISINTL11")
    survey_id = "462571962"
    try:
        response = sm_client.get_account_surveys()
        print(len(list(response)))
        # print(json.dumps(list(response), indent=4))

        # with open("temp/sisintl55_surveys_data.json", "w", encoding="utf-8") as file:
        #     json.dump(list(response), file, indent=4)

    except RuntimeError as e:
        print(str(e))


if __name__ == "__main__":
    main()