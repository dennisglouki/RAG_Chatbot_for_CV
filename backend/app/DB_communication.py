import os
import psycopg
import requests
from fastapi import HTTPException
from psycopg_pool import ConnectionPool


class Database:
    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL")
        self.pool = ConnectionPool(
            conninfo=self.database_url,
            min_size=1,
            max_size=5,
            open=True,
        )


    def get_connection(self):
        return self.pool.connection()

    def get_location(self, ip_address: str) -> dict:
        try:
            response = requests.get(
                f"https://api.ipapi.is/?q={ip_address}",
                timeout=2,
            )

            if response.status_code != 200:
                return {}

            data = response.json()
            return {
                "country": data.get("country"),
                "city": data.get("city"),
            }

        except requests.RequestException:
            return {}


    def get_daily_request_count(self, ip_address: str) -> int:
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT COUNT(*)
                    FROM chat_message AS m
                    JOIN chat_session AS s
                    ON s.id = m.session_id
                    WHERE s.ip_address = %s
                    AND m.created_at >= CURRENT_DATE
                    AND m.type = 'message'
                    """,
                    (ip_address,),
                )
                return cur.fetchone()[0]


    def lookup_id(self, slug: str) -> str:
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id
                    FROM customer
                    WHERE public_id = %s
                      AND status IN ('trial', 'active')
                    """,
                    (slug,),
                )
                row = cur.fetchone()

        if row is None:
            raise HTTPException(
                status_code=404,
                detail="Chatbot not found or inactive",
            )

        return str(row[0])

    def create_session(
        self,
        customer_id: str,
        ip_address: str | None = None,
        country: str | None = None,
        city: str | None = None,
    ) -> str:
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO chat_session (
                        customer_id,
                        ip_address,
                        country,
                        city
                    )
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                    """,
                    (customer_id, ip_address, country, city),
                )
                session_id = cur.fetchone()[0]

        return str(session_id)

    def validate_session(
        self,
        session_id: str,
        customer_id: str,
    ) -> bool:
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id
                    FROM chat_session
                    WHERE id = %s
                      AND customer_id = %s
                      AND expires_at > NOW()
                    """,
                    (session_id, customer_id),
                )
                return cur.fetchone() is not None

    def get_session_history(self, session_id: str) -> list[dict]:
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT question, answer
                    FROM chat_message
                    WHERE session_id = %s
                        AND type = 'message'
                      AND answer IS NOT NULL
                    ORDER BY created_at ASC, id 
                    limit 10"
                        
                    """,
                    (session_id,),
                )
                rows = cur.fetchall()

        history = []
        for question, answer in rows:
            history.append({"role": "user", "content": question})
            history.append({"role": "assistant", "content": answer})

        return history

    def store_request(
        self,
        session_id: str,
        question: str,
        answer: str | None,
        model: str | None = None,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        total_tokens: int | None = None,
        duration_s: float | None = None,
        status: str = "completed",
        type: str =  'message'
    ):
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO chat_message (
                        session_id,
                        question,
                        answer,
                        model,
                        input_tokens,
                        output_tokens,
                        total_tokens,
                        duration_s,
                        status,
                        type
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        session_id,
                        question,
                        answer,
                        model,
                        input_tokens,
                        output_tokens,
                        total_tokens,
                        duration_s,
                        status,
                        type
                    ),
                )

                cur.execute(
                    """
                    UPDATE chat_session
                    SET last_activity_at = NOW(),
                    expires_at = NOW() + INTERVAL '24 hours'
                    WHERE id = %s
                    """,
                    (session_id,),
                )

    def log_request(
        self,
        session_id: str,
        question: str | None,
        answer: str | None,
        meta: dict,
        duration_s: float | None = None,
        type: str = "message",
    ):
        self.store_request(
            session_id=session_id,
            question=question,
            answer=answer,
            model=meta.get("model"),
            input_tokens=meta.get("input_tokens"),
            output_tokens=meta.get("output_tokens"),
            total_tokens= meta.get("total_tokens"),
            duration_s=duration_s,
            status=meta.get("status", "completed"),
            type=type,
        )

    
    def consume_quota(self, quota_type: str, daily_limit: int) -> bool:
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO daily_global_quota
                        (quota_date, quota_type, request_count)
                    VALUES (CURRENT_DATE, %s, 1)
                    ON CONFLICT (quota_date, quota_type)
                    DO UPDATE SET
                        request_count =
                            daily_global_quota.request_count + 1
                    WHERE daily_global_quota.request_count < %s
                    RETURNING request_count
                    """,
                    (quota_type, daily_limit),
                )
                allowed = cur.fetchone() is not None

            conn.commit()

        return allowed
