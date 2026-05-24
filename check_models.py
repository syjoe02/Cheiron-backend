from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

try:
    models = client.models.list()

    for model in sorted(models.data, key=lambda x: x.id):
        print(model.id)
except Exception as e:
    print("Error:", e)