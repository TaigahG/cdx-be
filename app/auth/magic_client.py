from magic_admin import Magic
from dotenv import load_dotenv
import os

load_dotenv()

magic = Magic(api_secret_key=os.getenv("MAGIC_SECRET_KEY"))