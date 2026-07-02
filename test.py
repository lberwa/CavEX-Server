import os
import traceback
import psycopg2
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime

DB_URL = os.environ.get("DATABASE_URL")

def db_connect():
    if not DB_URL:
        raise Exception("DATABASE_URL ist nicht gesetzt!")

    print("Verbinde zur Datenbank...")
    return psycopg2.connect(
        DB_URL,
        sslmode="require",
        connect_timeout=10
    )

def datenbank_einrichten():
    try:
        conn = db_connect()
        print("Verbindung erfolgreich.")

        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS zugriffs_logs (
                id SERIAL PRIMARY KEY,
                zeitstempel TEXT NOT NULL
            );
        """)

        conn.commit()

        cursor.close()
        conn.close()

        print("Tabelle erfolgreich geprüft.")

    except Exception as e:
        print("\n========== DATENBANKFEHLER ==========")
        print(type(e).__name__)
        print(e)
        traceback.print_exc()
        print("=====================================\n")


class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):

        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()

        if not DB_URL:
            self.wfile.write(b"DATABASE_URL fehlt!")
            return

        try:
            conn = db_connect()
            cursor = conn.cursor()

            jetzt = datetime.now().strftime("%d.%m.%Y - %H:%M:%S Uhr")

            cursor.execute(
                "INSERT INTO zugriffs_logs (zeitstempel) VALUES (%s)",
                (jetzt,)
            )
            conn.commit()

            cursor.execute(
                "SELECT id, zeitstempel FROM zugriffs_logs ORDER BY id"
            )

            daten = cursor.fetchall()

            cursor.close()
            conn.close()

            text = "=== SUPABASE DATENBANK LOGS ===\n\n"

            for i, zeit in daten:
                text += f"Log-ID #{i}: Zugriff am {zeit}\n"

            self.wfile.write(text.encode("utf-8"))

        except Exception as e:
            traceback.print_exc()

            text = (
                "DATENBANKFEHLER\n\n"
                f"Typ: {type(e).__name__}\n\n"
                f"Fehler:\n{e}\n\n"
                "Hinweis:\n"
                "- Prüfe DATABASE_URL\n"
                "- Prüfe Netzwerk\n"
                "- Prüfe SSL\n"
                "- Prüfe, ob Render die Datenbank erreichen kann\n"
            )

            self.wfile.write(text.encode("utf-8"))


if __name__ == "__main__":

    print("DATABASE_URL vorhanden:", DB_URL is not None)

    datenbank_einrichten()

    port = int(os.environ.get("PORT", "10000"))

    print(f"Starte Server auf Port {port}")

    server = HTTPServer(("0.0.0.0", port), MyServer)

    server.serve_forever()
