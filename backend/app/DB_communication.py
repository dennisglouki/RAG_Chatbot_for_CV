import os
import psycopg
import requests


class Database:
    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL")

    def get_connection(self):
        return psycopg.connect(self.database_url)

    def get_daily_request_count(self, ip_address: str) -> int:
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT COUNT(*)
                    FROM llm_requests
                    WHERE ip_address = %s
                      AND created_at >= CURRENT_DATE
                    """,
                    (ip_address,),
                )

                return cur.fetchone()[0]
            
    def store_request(
        self,
        ip_address: str,
        question: str,
        answer: str,
        model: str,
        input_tokens: int | None,
        output_tokens: int | None,
        total_tokens: int | None,
        duration_ms: int | None = None,
        status: str = "completed",
        country: str = None,
        city: str = None 
    ):
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO llm_requests (
                        ip_address,
                        question,
                        answer,
                        model,
                        input_tokens,
                        output_tokens,
                        total_tokens,
                        duration_ms,
                        status,
                        country,
                        city
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s,%s,%s)
                    """,
                    (
                        ip_address,
                        question,
                        answer,
                        model,
                        input_tokens,
                        output_tokens,
                        total_tokens,
                        duration_ms,
                        status,
                        country,
                        city,
                    ),
                )

class GeoLocator:
    def get_location(self, ip_address):
        response = requests.get(
            f"https://api.ipapi.is/?q={ip_address}",
            timeout=1
    )

        if response.status_code != 200:
            return {}
        else: loc_response =response.json()
        location = {"country": loc_response.get("country"),
                    "city": loc_response.get("city")}    
        return location