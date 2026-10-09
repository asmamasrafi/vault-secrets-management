
import os

import hvac  # type: ignore[reportMissingModuleSource]
import psycopg2  # type: ignore[reportMissingModuleSource]
from flask import Flask, jsonify, render_template

app = Flask(__name__)


def get_database_credentials():
    """Authenticate to Vault with AppRole and read the database secret."""
    client = hvac.Client(url=os.environ["VAULT_ADDR"])

    client.auth.approle.login(
        role_id=os.environ["VAULT_ROLE_ID"],
        secret_id=os.environ["VAULT_SECRET_ID"],
    )

    if not client.is_authenticated():
        raise RuntimeError("Vault authentication failed")

    response = client.secrets.kv.v2.read_secret_version(
        path="vaultapp/db",
        mount_point="secret",
    )

    return response["data"]["data"]


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/database")
def database_page():
    return render_template("database.html")


@app.route("/secrets")
def secrets_page():
    return render_template("secrets.html")


@app.route("/logs")
def logs_page():
    return render_template("logs.html")

@app.route("/db-check")
def db_check():
    try:
        credentials = get_database_credentials()

        connection = psycopg2.connect(
            host=os.environ.get("DB_HOST", "postgres"),
            port=os.environ.get("DB_PORT", "5432"),
            dbname=credentials["database"],
            user=credentials["username"],
            password=credentials["password"],
            connect_timeout=5,
        )

        connection.close()

        return jsonify({
            "status": "success",
            "message": "Vault authentication and PostgreSQL connection successful",
        })

    except Exception:
        app.logger.exception("Database check failed")
        return jsonify({
            "status": "error",
            "message": "Database check failed. Check application logs.",
        }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)