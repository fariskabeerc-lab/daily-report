import streamlit as st
import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.mime.text import MIMEText
import os
from datetime import date

# --- Page Config ---
st.set_page_config(page_title="Outlet Daily Reporting System", layout="wide")

# --- Users Data ---
# Replace this with a database or CSV in production
users = {
    "manager1": {"password": "pass1", "role": "Manager", "outlet": "Outlet A", "email": "manager1@company.com"},
    "manager2": {"password": "pass2", "role": "Manager", "outlet": "Outlet B", "email": "manager2@company.com"},
    "supervisor": {"password": "superpass", "role": "Supervisor", "email": "supervisor@company.com"}
}

# --- Login ---
st.title("Outlet Daily Reporting System")
username = st.text_input("Username")
password = st.text_input("Password", type="password")

if st.button("Login"):
    if username in users and password == users[username]["password"]:
        role = users[username]["role"]
        st.success(f"Welcome {username} ({role})")

        # --- Outlet Manager View ---
        if role == "Manager":
            st.header("Upload Daily Report")
            uploaded_file = st.file_uploader("Upload Excel/CSV report", type=["xlsx", "csv"])
            extra_notes = st.text_area("Extra Notes / Problems")

            if uploaded_file is not None:
                # Save the uploaded file
                today = date.today().strftime("%Y-%m-%d")
                folder = "uploaded_reports"
                os.makedirs(folder, exist_ok=True)
                file_path = os.path.join(folder, f"{username}_{today}_{uploaded_file.name}")
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.success("File uploaded successfully!")

                # --- Send Email to Supervisor ---
                def send_email(to_email, subject, body, attachment):
                    from_email = "your_email@gmail.com"        # sender email
                    from_password = "your_app_password"        # app password

                    msg = MIMEMultipart()
                    msg['From'] = from_email
                    msg['To'] = to_email
                    msg['Subject'] = subject
                    msg.attach(MIMEText(body, 'plain'))

                    with open(attachment, "rb") as f:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(f.read())
                        encoders.encode_base64(part)
                        part.add_header('Content-Disposition', f"attachment; filename= {os.path.basename(attachment)}")
                        msg.attach(part)

                    server = smtplib.SMTP('smtp.gmail.com', 587)
                    server.starttls()
                    server.login(from_email, from_password)
                    server.send_message(msg)
                    server.quit()

                send_email(
                    to_email=users["supervisor"]["email"],
                    subject=f"Daily Report from {username} - {today}",
                    body=f"Outlet: {users[username]['outlet']}\nManager: {username}\nExtra Notes: {extra_notes}",
                    attachment=file_path
                )
                st.success("Email sent to supervisor successfully!")

        # --- Supervisor View ---
        elif role == "Supervisor":
            st.header("Supervisor Dashboard")
            folder = "uploaded_reports"
            os.makedirs(folder, exist_ok=True)

            files = os.listdir(folder)
            if len(files) == 0:
                st.info("No reports submitted yet.")
            else:
                report_list = []
                for f in files:
                    file_path = os.path.join(folder, f)
                    try:
                        if f.endswith(".csv"):
                            df = pd.read_csv(file_path)
                        else:
                            df = pd.read_excel(file_path)
                        df["Filename"] = f
                        report_list.append(df)
                    except:
                        continue

                if report_list:
                    all_reports = pd.concat(report_list, ignore_index=True)
                    st.dataframe(all_reports)
                else:
                    st.info("No valid reports found.")
    else:
        st.error("Invalid username or password")
