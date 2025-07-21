import os
import time
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import yfinance as yf
from rich.console import Console
from rich.table import Table
import smtplib
from email.mime.text import MIMEText

# Liste des actifs à surveiller
SYMBOLS = [
    'BTC-USD', 'ETH-USD', 'AAPL', 'MSFT'
    # Ajoute/enlève ce que tu veux !
]

T = '1h'  # Unité de temps des bougies ('1h', '1d', etc.)

# Variables d'environnement (plus de valeur en dur dans le code)
MAIL_FROM = os.getenv('MAIL_FROM')
MAIL_TO = os.getenv('MAIL_TO')
MAIL_PASS = os.getenv('MAIL_PASS')

console = Console()

def get_last_closes(symbol, timeframe, n=6):
    try:
        df = yf.download(symbol, period=f'{n+5}d', interval=timeframe, progress=False, auto_adjust=False)
        closes = df['Close'].dropna().values
        if len(closes) < 6:
            closes = [float('nan')] * (6 - len(closes)) + list(closes)
        return closes[-6:]
    except Exception as e:
        print(f"[{symbol}]: Erreur yfinance : {e}")
        return [float('nan')]*6

def check_signals(closes):
    # On tolère les valeurs NaN (manque de données)
    if any([pd.isna(c) for c in closes]):
        return "Données manquantes"
    C0, C1, C2, C3, C4, C5 = closes[::-1]  # C0 = la plus récente
    if (C2 > C3 and C2 > C4 and C2 > C5 and
        C1 < C2 and C1 < C3 and C1 < C4 and
        C0 > C1 and C0 > C2 and C0 > C3):
        return "AAAAAAAAAA"
    elif (C2 < C3 and C2 < C4 and C2 < C5 and
          C1 > C2 and C1 > C3 and C1 > C4 and
          C0 < C1 and C0 < C2 and C0 < C3):
        return "VVVVVVVVVV"
    else:
        return "Pas de signal"

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
        print(f"Erreur lors de l'envoi d'email : {e}")

def analyse_and_alert():
    found_signal = False
    body = ""
    results = []

    for symbol in SYMBOLS:
        closes = get_last_closes(symbol, T, 6)
        signal = check_signals(closes)
        results.append({
            'Actif': symbol,
            'Signal': signal,
            'C0': closes[::-1][0] if len(closes) == 6 else None,
            'C1': closes[::-1][1] if len(closes) == 6 else None,
            'C2': closes[::-1][2] if len(closes) == 6 else None,
            'C3': closes[::-1][3] if len(closes) == 6 else None,
            'C4': closes[::-1][4] if len(closes) == 6 else None,
            'C5': closes[::-1][5] if len(closes) == 6 else None,
        })
        if signal in ["AAAAAAAAAA", "VVVVVVVVVV"]:
            found_signal = True
            body += f"{symbol} : {signal}\n"

    # === AFFICHAGE BEAU ET COLORÉ AVEC RICH ===
    table = Table(title="Tableau des signaux multi-actifs")
    table.add_column("Actif", justify="center", style="bold cyan")
    table.add_column("Signal", justify="center")
    table.add_column("C0", justify="right")
    table.add_column("C1", justify="right")
    table.add_column("C2", justify="right")
    table.add_column("C3", justify="right")
    table.add_column("C4", justify="right")
    table.add_column("C5", justify="right")

    for row in results:
        signal = row['Signal']
        if signal == "AAAAAAAAAA":
            color = "bold green"
        elif signal == "VVVVVVVVVV":
            color = "bold red"
        elif signal == "Données manquantes":
            color = "yellow"
        else:
            color = "white"
        values = []
        for c in [row['C0'], row['C1'], row['C2'], row['C3'], row['C4'], row['C5']]:
            try:
                # Patch pour warning numpy : extraire la valeur si array
                if isinstance(c, np.ndarray):
                    v = float(c[0])
                else:
                    v = float(c)
                values.append(f"{v:.2f}")
            except Exception:
                values.append("--")
        table.add_row(row['Actif'], f"[{color}]{signal}[/{color}]", *values)

    console.print(table)
    # === FIN AFFICHAGE COLORÉ ===

    if found_signal:
        subject = "ALERTE TRADING BOT : Signal détecté"
        send_email(subject, body)
        print(f"Email envoyé !\n{body}")
    else:
        print("Aucun signal d'achat ou de vente. (Pas d'email envoyé)")

def wait_until_next_hour():
    now = datetime.utcnow()
    next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    sleep_seconds = (next_hour - now).total_seconds()
    print(f"Attente de {int(sleep_seconds)} secondes jusqu'à la prochaine heure pleine (UTC)...")
    time.sleep(sleep_seconds)

if __name__ == "__main__":
    while True:
        print("\n=== Analyse des signaux... ===")
        analyse_and_alert()
        wait_until_next_hour()

