import requests
import os
from dotenv import load_dotenv

load_dotenv()

# List voices (GET /v1/speech/voices)
response = requests.get(
  "https://api.murf.ai/v1/speech/voices",
  headers={
    "api-key": os.getenv('MURF_API_KEY')
  },
)

print(response.json())
