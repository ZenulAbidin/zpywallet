import time
from copy import deepcopy
from urllib.parse import urlparse

from ..generated import wallet_pb2


class DatabaseConnection:
    PLACEHOLDER = "?"
    BLOB_TYPE = "BLOB"

    def __init__(self, dbmodule, connection_params):
        self.dbmodule = dbmodule
        self.connection_params = self.parse_connection_params(connection_params)
        self.connection = None
        self.cursor = None

    def connect(self):
        self.connection = self.dbmodule.connect(**self.connection_params)
        self.cursor = self.connection.cursor()

    def disconnect(self):
        if self.connection:
            self.connection.close()
            self.connection = None
            self.cursor = None

    def reconnect(self):
        self.disconnect()
        self.connect()

    @staticmethod
    def parse_uri(uri):
        parsed_uri = urlparse(uri)
        if parsed_uri.scheme == "sqlite":
            database_path = parsed_uri.path
            if parsed_uri.netloc:
                database_path = f"/{parsed_uri.netloc}{parsed_uri.path}"
            elif database_path.startswith("//"):
                database_path = database_path[1:]
            return {
                "protocol": "sqlite",
                "database": database_path,
            }
        return {
            "protocol": parsed_uri.scheme,
            "host": parsed_uri.hostname,
            "port": parsed_uri.port,
            "database": parsed_uri.path.lstrip("/"),
            "user": parsed_uri.username,
            "password": parsed_uri.password,
        }

    @classmethod
    def parse_connection_params(cls, connection_params):
        if isinstance(connection_params, str):
            return cls.parse_uri(connection_params)
        return deepcopy(connection_params)

    def placeholders(self, count):
        return ", ".join([self.PLACEHOLDER] * count)

    def upsert_sql(self, table, columns, conflict_column):
        assignments = ", ".join(
            [
                f"{column} = EXCLUDED.{column}"
                for column in columns
                if column != conflict_column
            ]
        )
        column_list = ", ".join(columns)
        values = self.placeholders(len(columns))
        return (
            f"INSERT INTO {table} ({column_list}) VALUES ({values}) "
            + f"ON CONFLICT ({conflict_column}) DO UPDATE SET {assignments}"
        )


class PostgreSQLConnection(DatabaseConnection):
    PLACEHOLDER = "%s"
    BLOB_TYPE = "BYTEA"


class MySQLConnection(DatabaseConnection):
    PLACEHOLDER = "%s"
    BLOB_TYPE = "BLOB"

    def upsert_sql(self, table, columns, _conflict_column):
        column_list = ", ".join(columns)
        values = self.placeholders(len(columns))
        assignments = ", ".join([f"{column} = VALUES({column})" for column in columns])
        return (
            f"INSERT INTO {table} ({column_list}) VALUES ({values}) "
            + f"ON DUPLICATE KEY UPDATE {assignments}"
        )


class SQLiteConnection(DatabaseConnection):
    PLACEHOLDER = "?"
    BLOB_TYPE = "BLOB"

    def upsert_sql(self, table, columns, _conflict_column):
        column_list = ", ".join(columns)
        values = self.placeholders(len(columns))
        return f"INSERT OR REPLACE INTO {table} ({column_list}) VALUES ({values})"


class SQLTransactionStorage:
    def __init__(self, connection_params):
        self.connection_params = DatabaseConnection.parse_connection_params(
            connection_params
        )
        self.container = None

    def connect(self):
        if self.container:
            return

        protocol = self.connection_params["protocol"]
        params = deepcopy(self.connection_params)
        del params["protocol"]
        if protocol == "postgresql":
            import psycopg2

            self.container = PostgreSQLConnection(psycopg2, params)
        elif protocol == "mysql":
            import mysql.connector

            self.container = MySQLConnection(mysql.connector, params)
        elif protocol == "sqlite":
            import sqlite3

            self.container = SQLiteConnection(sqlite3, params)
        else:
            raise ValueError("Unsupported protocol")

        self.container.connect()

        try:
            self.create_metadata_table()
            self.create_transactions_table()
            self.create_txos_table()
            self._ensure_txid_column_capacity()
        except DatabaseError:
            self.rollback()
            self.disconnect()
            self.container = None
            raise

    def disconnect(self):
        if self.container:
            self.container.disconnect()

    def reconnect(self):
        if self.container:
            self.container.reconnect()

    def commit(self):
        if self.container:
            self.container.connection.commit()

    def rollback(self):
        try:
            if self.container:
                self.container.connection.rollback()
        except Exception:
            pass

    def _execute(self, sql, params=None):
        if not self.container:
            self.connect()
        self.container.cursor.execute(sql, params or ())

    def _fetchone_value(self, sql, params=None, default=None):
        self._execute(sql, params)
        result = self.container.cursor.fetchone()
        if result is None:
            return default
        return result[0]

    def _store_tx_reference(self, txid, address, tx_index, entry_type):
        if not address:
            return
        sql = self.container.upsert_sql(
            "txos",
            ["txid", "address", "tx_index", "entry_type"],
            "txid, address, tx_index, entry_type",
        )
        self._execute(sql, (txid, address, tx_index, entry_type))

    def _sql_to_protobuf(self, row):
        if not row:
            return None
        transaction = wallet_pb2.Transaction()
        transaction.ParseFromString(row[0])
        return transaction

    def clear_transactions(self):
        try:
            self._execute("DELETE FROM txos")
            self._execute("DELETE FROM transactions")
        except Exception as e:
            raise DatabaseError(f"Error clearing transactions: {e}")

    def create_metadata_table(self):
        try:
            self._execute(
                """
                CREATE TABLE IF NOT EXISTS metadata (
                    zpywallet_const VARCHAR(32) PRIMARY KEY,
                    height INTEGER
                )
                """
            )
            existing = self._fetchone_value(
                f"""
                SELECT COUNT(zpywallet_const) FROM metadata
                WHERE zpywallet_const = {self.container.PLACEHOLDER}
                """,
                ("zpywallet",),
                default=0,
            )
            if not existing:
                self._execute(
                    f"""
                    INSERT INTO metadata (zpywallet_const, height)
                    VALUES ({self.container.placeholders(2)})
                    """,
                    ("zpywallet", 0),
                )
        except Exception as e:
            raise DatabaseError(f"Error creating table: {e}")

    def create_transactions_table(self):
        try:
            self._execute(
                """
                CREATE TABLE IF NOT EXISTS transactions (
                    txid VARCHAR(66) PRIMARY KEY,
                    timestamp TIMESTAMP,
                    confirmed BOOLEAN,
                    height BIGINT,
                    total_fee BIGINT,
                    fee_metric INTEGER,
                    rawtx BLOB,
                    txfrom TEXT,
                    txto TEXT,
                    amount INTEGER,
                    gas INTEGER,
                    data BLOB
                )
                """
            )
            self._execute(
                """
                CREATE VIEW IF NOT EXISTS confirmed_transactions AS
                SELECT * FROM transactions WHERE confirmed = TRUE
                """
            )
            self._execute(
                """
                CREATE VIEW IF NOT EXISTS unconfirmed_transactions AS
                SELECT * FROM transactions WHERE confirmed = FALSE
                """
            )
        except Exception as e:
            raise DatabaseError(f"Error creating transactions table: {e}")

    def create_txos_table(self):
        try:
            self._execute(
                """
                CREATE TABLE IF NOT EXISTS txos (
                    txid VARCHAR(66),
                    address TEXT,
                    tx_index INTEGER,
                    entry_type TEXT,
                    PRIMARY KEY (txid, address, tx_index, entry_type)
                )
                """
            )
        except Exception as e:
            raise DatabaseError(f"Error creating txos table: {e}")

    def _ensure_txid_column_capacity(self):
        try:
            protocol = self.connection_params["protocol"]
            if protocol == "postgresql":
                statements = [
                    "ALTER TABLE transactions ALTER COLUMN txid TYPE VARCHAR(66)",
                    "ALTER TABLE txos ALTER COLUMN txid TYPE VARCHAR(66)",
                ]
            elif protocol == "mysql":
                statements = [
                    "ALTER TABLE transactions MODIFY COLUMN txid VARCHAR(66) NOT NULL",
                    "ALTER TABLE txos MODIFY COLUMN txid VARCHAR(66) NOT NULL",
                ]
            else:
                return

            for statement in statements:
                self._execute(statement)
        except Exception as e:
            raise DatabaseError(f"Error widening txid columns: {e}")

    def get_block_height(self):
        try:
            if not self.container:
                self.connect()
            height = self._fetchone_value(
                f"""
                SELECT height FROM metadata
                WHERE zpywallet_const = {self.container.PLACEHOLDER}
                """,
                ("zpywallet",),
                default=0,
            )
            return 0 if height is None else height
        except Exception as e:
            raise DatabaseError(f"Error getting block height from database: {e}")

    def set_block_height(self, height):
        try:
            if not self.container:
                self.connect()
            sql = self.container.upsert_sql(
                "metadata", ["zpywallet_const", "height"], "zpywallet_const"
            )
            self._execute(sql, ("zpywallet", height))
        except Exception as e:
            raise DatabaseError(f"Error setting block height in database: {e}")

    def store_transaction(self, transaction):
        try:
            if not self.container:
                self.connect()
            sql = self.container.upsert_sql(
                "transactions",
                [
                    "txid",
                    "timestamp",
                    "confirmed",
                    "height",
                    "total_fee",
                    "fee_metric",
                    "rawtx",
                    "txfrom",
                    "txto",
                    "amount",
                    "gas",
                    "data",
                ],
                "txid",
            )
            data = (
                transaction.txid,
                transaction.timestamp,
                transaction.confirmed,
                transaction.height,
                transaction.total_fee,
                transaction.fee_metric,
                transaction.SerializeToString(),
                transaction.ethlike_transaction.txfrom or "",
                transaction.ethlike_transaction.txto or "",
                transaction.ethlike_transaction.amount,
                transaction.ethlike_transaction.gas,
                bytes(transaction.ethlike_transaction.data or b""),
            )
            self._execute(sql, data)

            self._execute(
                f"DELETE FROM txos WHERE txid = {self.container.PLACEHOLDER}",
                (transaction.txid,),
            )

            for tx_index, txinput in enumerate(transaction.btclike_transaction.inputs):
                self._store_tx_reference(
                    transaction.txid, txinput.address, tx_index, "input"
                )
            for tx_index, txoutput in enumerate(transaction.btclike_transaction.outputs):
                self._store_tx_reference(
                    transaction.txid, txoutput.address, tx_index, "output"
                )
            self._store_tx_reference(
                transaction.txid, transaction.ethlike_transaction.txfrom, 0, "from"
            )
            self._store_tx_reference(
                transaction.txid, transaction.ethlike_transaction.txto, 0, "to"
            )
        except Exception as e:
            raise DatabaseError(f"Error storing transaction: {e}")

    def have_transaction(self, txid):
        try:
            if not self.container:
                self.connect()
            count = self._fetchone_value(
                f"SELECT COUNT(txid) FROM transactions WHERE txid = {self.container.PLACEHOLDER} LIMIT 1",
                (txid,),
                default=0,
            )
            return count > 0
        except Exception as e:
            raise DatabaseError(f"Error deleting transaction: {e}")

    def delete_dropped_txids(self):
        try:
            if not self.container:
                self.connect()
            cutoff = int(time.time()) - 1209600
            self._execute(
                f"""
                DELETE FROM txos WHERE txid IN (
                    SELECT txid FROM transactions
                    WHERE confirmed = FALSE AND timestamp < {self.container.PLACEHOLDER}
                )
                """,
                (cutoff,),
            )
            self._execute(
                f"""
                DELETE FROM transactions
                WHERE confirmed = FALSE AND timestamp < {self.container.PLACEHOLDER}
                """,
                (cutoff,),
            )
        except Exception as e:
            raise DatabaseError(f"Error deleting transaction: {e}")

    def delete_transaction(self, txid):
        try:
            if not self.container:
                self.connect()
            data = (txid,)
            self._execute(
                f"DELETE FROM transactions WHERE txid = {self.container.PLACEHOLDER}",
                data,
            )
            self._execute(
                f"DELETE FROM txos WHERE txid = {self.container.PLACEHOLDER}", data
            )
        except Exception as e:
            raise DatabaseError(f"Error deleting transaction: {e}")

    def get_transaction_by_txid(self, txid):
        try:
            if not self.container:
                self.connect()
            self._execute(
                f"SELECT rawtx FROM transactions WHERE txid = {self.container.PLACEHOLDER}",
                (txid,),
            )
            result = self.container.cursor.fetchone()
            return self._sql_to_protobuf(result)
        except Exception as e:
            raise DatabaseError(f"Error getting transaction by txid: {e}")

    def get_transactions_by_address(self, address):
        try:
            if not self.container:
                self.connect()
            self._execute(
                f"""
                SELECT DISTINCT t.rawtx
                FROM transactions t
                JOIN txos x ON x.txid = t.txid
                WHERE x.address = {self.container.PLACEHOLDER}
                ORDER BY t.confirmed DESC, t.height ASC, t.timestamp ASC
                """,
                (address,),
            )
            rows = self.container.cursor.fetchall()
            return [self._sql_to_protobuf(row) for row in rows if row]
        except Exception as e:
            raise DatabaseError(f"Error storing txo: {e}")


class DatabaseError(Exception):
    pass
