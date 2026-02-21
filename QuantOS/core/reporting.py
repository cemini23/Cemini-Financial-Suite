import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import datetime
import os

class SunsetReporter:
    def __init__(self, recipients=None):
        # Use provided recipients list or fallback to environment string
        if isinstance(recipients, str):
            self.recipients = [r.strip() for r in recipients.split(",")]
        elif isinstance(recipients, list):
            self.recipients = recipients
        else:
            env_recipients = os.getenv("REPORT_RECIPIENTS", "")
            self.recipients = [r.strip() for r in env_recipients.split(",") if r.strip()]
        
        self.smtp_server = "smtp.gmail.com"
        self.port = 587
        self.sender = os.getenv("REPORT_EMAIL")
        self.password = os.getenv("REPORT_PASSWORD")

    def generate_html_report(self, pnl_data):
        """Creates a professional HTML email body."""
        total_pnl = sum(pnl_data.values())
        color = "green" if total_pnl >= 0 else "red"
        
        rows = "".join([f"<tr><td>{k}</td><td>${v:,.2f}</td></tr>" for k, v in pnl_data.items()])
        
        return f"""
        <html>
            <body style="font-family: Arial; color: #333;">
                <h2 style="color: #001f3f;">QuantOS: Sunset Report</h2>
                <p>Date: {datetime.date.today()}</p>
                <hr>
                <div style="font-size: 24px; font-weight: bold; color: {color};">
                    Total Daily P&L: ${total_pnl:,.2f}
                </div>
                <table border="1" cellpadding="10" style="border-collapse: collapse; width: 100%; margin-top: 20px;">
                    <tr style="background-color: #f2f2f2;"><th>Broker</th><th>Daily Change</th></tr>
                    {rows}
                </table>
                <p style="font-size: 12px; color: #777; margin-top: 30px;">
                    Confidential Report for Claudio Barone Jr. & Claudio Barone Sr.
                </p>
            </body>
        </html>
        """

    def send_report(self, pnl_data):
        """Logs into SMTP and fires the emails."""
        try:
            if not self.sender or not self.password:
                print("⚠️ Report Error: REPORT_EMAIL or REPORT_PASSWORD not set in environment.")
                return

            msg = MIMEMultipart()
            msg['From'] = self.sender
            msg['To'] = ", ".join(self.recipients)
            msg['Subject'] = f"📊 QuantOS Daily Summary: {datetime.date.today()}"
            
            body = self.generate_html_report(pnl_data)
            msg.attach(MIMEText(body, 'html'))
            
            with smtplib.SMTP(self.smtp_server, self.port) as server:
                server.starttls()
                server.login(self.sender, self.password)
                server.send_message(msg)
            print("📬 SUNSET REPORT: Emails sent successfully.")
        except Exception as e:
            print(f"⚠️ Report Error: {e}")
