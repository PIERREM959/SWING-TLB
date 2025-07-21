from rich.console import Console
from rich.table import Table
import yfinance as yf
import pandas as pd
import time
import smtplib
from email.mime.text import MIMEText

# === CONFIG ===
SYMBOLS = ['BTC-USD', 'ETH-USD', 'AAPL', 'MSFT']
T = '1h'
MAIL_FROM = 'tonadresse@gmail.com'          # pierrem959@gmail.com
MAIL_TO = 'destinataire@gmail.com'          # pierrem959@gmail.com
MAIL_PASS = 'MOT_DE_PASSE_APPLICATION'      # xerpozfnqzggodyq

def get_last_closes(symbol, timeframe, n=6):
    df = yf.download(symbol, period=f'{n+5}d', interval=timeframe, progress=False, auto_adjust=False)

    closes = df['Close'].dropna().values
    if len(closes) < 6:
        closes = [float('nan')] * (6 - len(closes)) + list(closes)
    return closes[-6:]

def check_signals(closes):
    if len(closes) < 6 or any(pd.isna(c) for c in closes):
        return "Données manquantes"
    C0, C1, C2, C3, C4, C5 = closes[::-1]
    if (C2 > C3 and C2 > C4 and C2 > C5) and \
       (C1 < C2 and C1 < C3 and C1 < C4) and \
       (C0 > C1 and C0 > C2 and C0 > C3):
        return "A" * 10
    elif (C2 < C3 and C2 < C4 and C2 < C5) and \
         (C1 > C2 and C1 > C3 and C1 > C4) and \
         (C0 < C1 and C0 < C2 and C0 < C3):
        return "V" * 10
    else:
        return "Pas de signal"

def send_email(subject, body, mail_from=MAIL_FROM, mail_to=MAIL_TO, mail_pass=MAIL_PASS):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = mail_from
    msg['To'] = mail_to

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(mail_from, mail_pass)
        server.send_message(msg)
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
    console = Console()
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

if __name__ == "__main__":
    while True:
        print("=== Analyse des signaux... ===")
        analyse_and_alert()
        print("Attente de 1 heure...\n")
        time.sleep(3600)  # 3600 secondes = 1 heure
