import yfinance as yf
import pandas as pd
import time
import smtplib
from email.mime.text import MIMEText

# === CONFIG ===
SYMBOLS = ['BTC-USD', 'ETH-USD', 'AAPL', 'MSFT']
T = '1h'
MAIL_FROM = 'tonadresse@gmail.com'          # <-- Mets ton adresse gmail ici
MAIL_TO = 'destinataire@gmail.com'          # <-- Mets l'adresse de destination
MAIL_PASS = 'MOT_DE_PASSE_APPLICATION'      # <-- Mets ici le mot de passe d'application Gmail

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
    for symbol in SYMBOLS:
        closes = get_last_closes(symbol, T, 6)
        signal = check_signals(closes)
        if signal in ["AAAAAAAAAA", "VVVVVVVVVV"]:
            found_signal = True
            body += f"{symbol} : {signal}\n"
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
