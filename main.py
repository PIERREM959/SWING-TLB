import os
import time
from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf
from rich.console import Console
from rich.table import Table
import smtplib
from email.mime.text import MIMEText

# Liste des actifs à surveiller
SYMBOLS = ['GDAXI']  # Indice DAX

T = '1h'  # Unité de temps

# Variables d'environnement pour l'e-mail
MAIL_FROM = os.getenv('MAIL_FROM')
MAIL_TO = os.getenv('MAIL_TO')
MAIL_PASS = os.getenv('MAIL_PASS')

console = Console()

# === Variables de trading ===
open_position = False
entry_price = None
stop_price = None
TRAILING_STOP_PCT = 0.01  # 1%

def get_last_closes(symbol, timeframe):
    try:
        df = yf.download(symbol, period='3d', interval=timeframe, progress=False, auto_adjust=False)
        closes = df['Close'].dropna().values
        if len(closes) < 2:
            return None, None
        return closes[-1], closes[-2]  # C0 (dernier), C1 (précédent)
    except Exception as e:
        print(f"[{symbol}]: Erreur yfinance : {e}")
        return None, None

def send_email(subject, body):
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = MAIL_FROM
        msg['To'] = MAIL_TO
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(MAIL_FROM, MAIL_PASS)
            server.sendmail(MAIL_FROM, MAIL_TO, msg.as_string())
        print(f"Email envoyé : {subject}")
    except Exception as e:
        print(f"Erreur envoi email : {e}")

def analyse_and_trade():
    global open_position, entry_price, stop_price

    table = Table(title="Signaux & Positions")
    table.add_column("Message", justify="center", style="bold cyan")

    for symbol in SYMBOLS:
        C0, C1 = get_last_closes(symbol, T)
        if not C0 or not C1:
            table.add_row("Données manquantes")
            continue

        message = ""

        if not open_position:
            # Signal d'achat si C0 > C1
            if C0 > C1:
                open_position = True
                entry_price = C0
                stop_price = entry_price * (1 - TRAILING_STOP_PCT)
                message = f"ACHAT DAX à {entry_price:.2f} points"
                send_email("ALERTE TRADING BOT", message)
        else:
            # Si position ouverte, vérifier trailing stop
            if C0 <= stop_price:
                message = f"VENTE DAX à {C0:.2f} points"
                send_email("ALERTE TRADING BOT", message)
                # Reset position
                open_position = False
                entry_price = None
                stop_price = None
            else:
                # Si prix monte, on ajuste le trailing stop
                if C0 > entry_price:
                    stop_price = max(stop_price, C0 * (1 - TRAILING_STOP_PCT))
                message = f"Position ouverte, prix actuel {C0:.2f}, stop {stop_price:.2f}"

        if message:
            table.add_row(message)

    console.print(table)

def wait_until_next_hour():
    now = datetime.utcnow()
    next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    sleep_seconds = (next_hour - now).total_seconds()
    print(f"Attente {int(sleep_seconds)} sec jusqu'à la prochaine heure pleine (UTC)...")
    time.sleep(sleep_seconds)

if __name__ == "__main__":
    while True:
        print("\n=== Analyse des signaux... ===")
        analyse_and_trade()
        wait_until_next_hour()
