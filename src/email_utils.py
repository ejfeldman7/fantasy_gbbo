import smtplib
from email.message import EmailMessage
from email.utils import formataddr
from typing import Any, Dict

import pandas as pd
import streamlit as st


def send_confirmation_email(
    recipient_email: str, user_name: str, week_display: str, picks: Dict[str, Any]
):
    """Sends a confirmation email to the user with their submitted picks."""
    try:
        creds = st.secrets["email_credentials"]
        sender_name, sender_email, sender_password = (
            creds["sender_name"],
            creds["sender_email"],
            creds["sender_password"],
        )
    except (KeyError, FileNotFoundError):
        st.warning(
            "Email credentials not configured. Email not sent.",
            icon="⚠️",
        )
        return

    msg = EmailMessage()
    msg["Subject"] = f"🧁 Bake Off Fantasy Picks Confirmation - {week_display}"
    msg["From"] = formataddr((sender_name, sender_email))
    msg["To"] = recipient_email
    body = f"""
    <html><body><div style="font-family:sans-serif;padding:20px;border:1px solid #ddd;border-radius:8px;max-width:600px;">
        <h2>Hi {user_name},</h2><p>Your fantasy picks for <strong>{week_display}</strong> have been submitted!</p>
        <h4>Weekly Picks:</h4><ul>
            <li><strong>⭐ Star Baker:</strong> {picks.get('star_baker', 'N/A')}</li>
            <li><strong>🏆 Technical Winner:</strong> {picks.get('technical_winner', 'N/A')}</li>
            <li><strong>😢 Eliminated Baker:</strong> {picks.get('eliminated_baker', 'N/A')}</li>
            <li><strong>🤝 Handshake:</strong> {'Yes' if picks.get('hollywood_handshake') else 'No'}</li>
        </ul>
        <h4>Season Predictions:</h4><ul>
            <li><strong>👑 Season Winner:</strong> {picks.get('season_winner', 'N/A')}</li>
            <li><strong>🥈 Finalist A:</strong> {picks.get('finalist_2', 'N/A')}</li>
            <li><strong>🥈 Finalist B:</strong> {picks.get('finalist_3', 'N/A')}</li>
        </ul></div></body></html>
    """
    msg.set_content("This is a fallback for plain-text email clients.")
    msg.add_alternative(body, subtype="html")
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(sender_email, sender_password)
            smtp.send_message(msg)
        st.info(f"A confirmation email was sent to {recipient_email}.")
    except Exception as e:
        st.error(f"Failed to send confirmation email. Error: {e}")


def send_commissioner_update_email(
    week_display: str, results: Dict[str, Any], scores_df: pd.DataFrame
):
    """Sends an update email to the commissioner with weekly results and leaderboard."""
    try:
        creds = st.secrets["email_credentials"]
        sender_name, sender_email, sender_password = (
            creds["sender_name"],
            creds["sender_email"],
            creds["sender_password"],
        )
        commissioner_email = sender_email
    except (KeyError, FileNotFoundError):
        st.warning("Email credentials not configured. Commissioner update not sent.", icon="⚠️")
        return

    msg = EmailMessage()
    msg["Subject"] = f"🏆 Bake Off Weekly Results & Leaderboard - {week_display}"
    msg["From"] = formataddr((sender_name, sender_email))
    msg["To"] = commissioner_email
    scores_html = scores_df.to_html(index=True, border=0, classes="dataframe")
    body = f"""
    <html><head><style>
        body{{font-family:sans-serif;}} .container{{padding:20px;border:1px solid #ddd;border-radius:8px;max-width:600px;}}
        h2,h3{{color:#333;}} table.dataframe{{border-collapse:collapse;width:100%;margin-bottom:20px;}}
        table.dataframe th,table.dataframe td{{border:1px solid #ddd;padding:8px;text-align:left;}}
        table.dataframe th{{background-color:#f2f2f2;}}
    </style></head><body><div class="container">
        <h2>Results for {week_display} have been entered!</h2>
        <h3>Summary of Results:</h3><ul>
            <li><strong>⭐ Star Baker:</strong> {results.get('star_baker', 'N/A')}</li>
            <li><strong>🏆 Technical Winner:</strong> {results.get('technical_winner', 'N/A')}</li>
            <li><strong>😢 Eliminated Baker:</strong> {results.get('eliminated_baker', 'N/A')}</li>
            <li><strong>🤝 Handshake Given:</strong> {'Yes' if results.get('handshake_given') else 'No'}</li>
        </ul><h3>Updated Leaderboard:</h3>{scores_html}
    </div></body></html>
    """
    msg.set_content("This is a fallback for plain-text email clients.")
    msg.add_alternative(body, subtype="html")
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(sender_email, sender_password)
            smtp.send_message(msg)
        st.info(f"An update email has been sent to the commissioner at {commissioner_email}.")
    except Exception as e:
        st.error(f"Failed to send commissioner update email. Error: {e}")
