import os
import time
from datetime import datetime, timedelta
import pytz
import pandas as pd
import yfinance as yf
from rich.console import Console
from rich.table import Table
import smtplib
from email.mime.text import MIMEText

# === Config ===
SYMBOLS = ['^GDAXI']
T = '1h'
TRAILING_STOP_PCT = 0.01  # 1%
START_HOUR = 9    # Heure d'ouverture
END_HOUR = 17.5   # Heure de fermeture (17h30)
TIMEZONE = pytz.timezone("Europe/Paris")

MAIL_FROM = os.getenv('MAIL_FROM')
MAIL_TO = os.getenv('MAIL_TO')
MAIL_PASS = os.getenv('MAIL_PASS')

console = Console()

# Variables de position
open_position = False
entry_price = None
stop_price = None


def get_last_closes(symbol, timeframe):
    try:
        df = yf.download(symbol, period='3d', interval=timeframe, progress=False, auto_adjust=False)
        closes = df['Close'].dropna().values
        if len(closes) < 2:
            return None, None
        return closes[-1], closes[-2]
    except Exception as e:
        print(f"[{symbol}] Erreur yfinance : {e}")
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
        print(f"Email envoyé : {subject}")
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
            if C0 > C1:
                open_position = True
                entry_price = C0
                stop_price = entry_price * (1 - TRAILING_STOP_PCT)
                message = f"ACHAT DAX à {entry_price:.2f} points"
                send_email("ALERTE TRADING BOT", message)
        else:
            if C0 <= stop_price:
                message = f"VENTE DAX à {C0:.2f} points (Stop atteint)"
                send_email("ALERTE TRADING BOT", message)
                open_position = False
                entry_price = None
                stop_price = None
            else:
                if C0 > entry_price:
                    stop_price = max(stop_price, C0 * (1 - TRAILING_STOP_PCT))
                message = f"Position ouverte - Prix: {C0:.2f}, Stop: {stop_price:.2f}"

        if message:
            table.add_row(message)

    console.print(table)


def close_position_if_market_closed(C0):
    global open_position, entry_price, stop_price

    if open_position:
        message = f"VENTE AUTO 17h30 DAX à {C0:.2f} points"
        send_email("ALERTE TRADING BOT", message)
        open_position = False
        entry_price = None
        stop_price = None
        console.print(f"[bold red]{message}[/bold red]")


def wait_until_next_hour():
    now = datetime.utcnow()
    next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    time.sleep((next_hour - now).total_seconds())


if __name__ == "__main__":
    while True:
        now_paris = datetime.now(TIMEZONE)
        current_hour = now_paris.hour + now_paris.minute / 60

        if START_HOUR <= current_hour <= END_HOUR:
            print(f"\n=== {now_paris.strftime('%H:%M')} - Analyse des signaux... ===")
            analyse_and_trade()
        else:
            print(f"{now_paris.strftime('%H:%M')} - Hors heures de trading (standby)...")

            # Si marché fermé et position ouverte, fermeture auto à 17h30
            if open_position and current_hour > END_HOUR:
                C0, _ = get_last_closes(SYMBOLS[0], T)
                if C0:
                    close_position_if_market_closed(C0)

        wait_until_next_hour()
