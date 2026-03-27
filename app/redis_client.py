import redis
import os
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL")

redis_client = None

def get_redis()-> redis.Redis:
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url(
            REDIS_URL,
            decode_responses=True,
            max_connections=20,
            socket_timeout=5,
            socket_connect_timeout=5,
        )
    return redis_client

def close_redis():
    global redis_client
    if redis_client is not None:
        redis_client.close()
        redis_client = None

        
