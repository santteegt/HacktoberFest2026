import time
import psycopg2
import os
from twelvedata import TDClient
from psycopg2.extras import execute_values
from datetime import datetime, timezone


class WebsocketPipeline:
    # name of the hypertable
    DB_TABLE = "crypto_ticks"

    # columns in the hypertable in the correct order
    DB_COLUMNS = ["time", "symbol", "price", "day_volume"]

    # batch size used to insert data in batches (keep small while validating the pipeline)
    MAX_BATCH_SIZE = 10

    def __init__(self, conn):
        """Connect to the Twelve Data web socket server and stream
        data into the database.

        Args:
            conn: psycopg2 connection object
        """
        self.conn = conn
        self.current_batch = []
        self.insert_counter = 0

    def _insert_values(self, data):
        if self.conn is not None and data:
            cursor = self.conn.cursor()
            sql = f"""
            INSERT INTO {self.DB_TABLE} ({','.join(self.DB_COLUMNS)})
            VALUES %s;"""
            execute_values(cursor, sql, data)
            self.conn.commit()

    def _flush_batch(self):
        """Write any buffered rows, then clear the batch."""
        if not self.current_batch:
            return
        self._insert_values(self.current_batch)
        self.insert_counter += 1
        print(f"Batch insert #{self.insert_counter} ({len(self.current_batch)} rows)")
        self.current_batch = []

    def _on_event(self, event):
        """This function gets called whenever there's a new data record coming
        back from the server.

        Args:
            event (dict): data record
        """
        kind = event.get("event")

        if kind == "subscribe-status":
            print(
                f"subscribe-status: status={event.get('status')} "
                f"success={event.get('success')} fails={event.get('fails')}"
            )
            return

        if kind == "price":
            timestamp = datetime.fromtimestamp(event["timestamp"], tz=timezone.utc)
            data = (timestamp, event["symbol"], event["price"], event.get("day_volume"))

            self.current_batch.append(data)
            print(f"Current batch size: {len(self.current_batch)}")

            if len(self.current_batch) >= self.MAX_BATCH_SIZE:
                self._flush_batch()

    def start(self, symbols):
        """Connect to the web socket server and start streaming real-time data
        into the database.

        Args:
            symbols (list of symbols): List of stock/crypto symbols
        """
        td = TDClient(apikey=os.getenv("TWELVEDATA_API_KEY"), log_level="info")
        ws = td.websocket(on_event=self._on_event)
        ws.subscribe(symbols)
        ws.connect()
        try:
            while True:
                ws.heartbeat()
                time.sleep(10)
        except KeyboardInterrupt:
            print("Stopping; flushing remaining batch…")
            self._flush_batch()
            ws.disconnect()
            print("Stopped.")


if __name__ == "__main__":
    conn = psycopg2.connect(
        database="tsdb",
        host=os.getenv("TD_HOST"),
        user="tsdbadmin",
        password=os.getenv("TD_PASSWORD"),
        port=os.getenv("TD_PORT"),
        sslmode="require",
    )

    # Free-tier WS credits often allow only ~2 concurrent symbols; keep the list short.
    symbols = ["BTC/USD", "ETH/USD"]
    websocket = WebsocketPipeline(conn)
    websocket.start(symbols=symbols)
