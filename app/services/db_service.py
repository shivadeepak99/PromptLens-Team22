import os
from contextlib import contextmanager
from typing import Any

from dotenv import load_dotenv
from psycopg2.pool import SimpleConnectionPool
from psycopg2.extras import RealDictCursor


class DatabaseNotInitializedError(RuntimeError):
	"""Raised when database pool is used before startup initialization."""


class DatabaseService:
	def __init__(self) -> None:
		self.pool: SimpleConnectionPool | None = None

	def init_pool(self) -> None:
		if self.pool is not None:
			return

		# Ensure .env variables are loaded before reading DATABASE_* settings.
		load_dotenv()

		database_url = os.getenv(
			"DATABASE_URL",
			"postgresql://postgres:supersecret@localhost:5432/promptlens",
		)
		min_conn = int(os.getenv("DATABASE_MIN_CONN", "1"))
		max_conn = int(os.getenv("DATABASE_MAX_CONN", "20"))

		self.pool = SimpleConnectionPool(
			minconn=min_conn,
			maxconn=max_conn,
			dsn=database_url,
		)

	def close_pool(self) -> None:
		if self.pool is not None:
			self.pool.closeall()
			self.pool = None

	@contextmanager
	def get_conn(self):
		if self.pool is None:
			raise DatabaseNotInitializedError("Database pool has not been initialized")

		conn = self.pool.getconn()
		try:
			yield conn
		finally:
			self.pool.putconn(conn)

	def fetch_all(self, query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
		with self.get_conn() as conn:
			with conn.cursor(cursor_factory=RealDictCursor) as cursor:
				cursor.execute(query, params)
				rows = cursor.fetchall()
				return [dict(row) for row in rows]

	def fetch_one(self, query: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
		with self.get_conn() as conn:
			with conn.cursor(cursor_factory=RealDictCursor) as cursor:
				cursor.execute(query, params)
				row = cursor.fetchone()
				return dict(row) if row else None


db_service = DatabaseService()
