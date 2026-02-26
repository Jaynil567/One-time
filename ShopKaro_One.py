from flask import Flask, render_template, redirect, url_for, request
import mysql.connector
import json, os

from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

# ---------- CONFIG ----------
app = Flask(__name__)
app.secret_key = "setup-secret"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

CLIENT_SECRET = json.loads(os.getenv("clint_secret"))

# ---------- DB ----------
def db():
    return mysql.connector.connect(
        host="centerbeam.proxy.rlwy.net",
        user="root",
        password="GZFvMhflsqtzEyFBvPOnNtrapaJWNqhF",
        database="railway",
        port=11620
    )

# ---------- HOME ----------
@app.route("/")
def home():
    return render_template("Home.html")

# ---------- SETUP CLICK ----------
@app.route("/setup")
def setup():

    flow = Flow.from_client_config(
        CLIENT_SECRET,
        scopes=SCOPES,
        redirect_uri=url_for("callback", _external=True)
    )

    auth_url, state = flow.authorization_url(prompt="consent")
    return redirect(auth_url)

# ---------- CALLBACK ----------
@app.route("/callback")
def callback():

    flow = Flow.from_client_config(
        CLIENT_SECRET,
        scopes=SCOPES,
        redirect_uri=url_for("callback", _external=True)
    )

    flow.fetch_token(authorization_response=request.url)
    creds = flow.credentials

    token_json = creds.to_json()

    # ---- Save token in DB ----
    conn = db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE ShopKaro_mediator
        SET token=%s
        WHERE username='shopkaro1'
    """, (token_json,))

    conn.commit()
    cur.close()
    conn.close()

    # ---- Create Sheet ----
    sheets_service = build("sheets", "v4", credentials=creds)
    drive_service = build("drive", "v3", credentials=creds)

    spreadsheet = {
        "properties": {
            "title": "ShopKaro"
        }
    }

    sheet = sheets_service.spreadsheets().create(
        body=spreadsheet,
        fields="spreadsheetId,spreadsheetUrl"
    ).execute()

    sheet_id = sheet["spreadsheetId"]
    sheet_url = sheet["spreadsheetUrl"]

    # ---- Header ----
    headers = [[
        "TimeStamp","Brand Name","Profile Name","Order Date",
        "Product Name","Order SS","Order Amount","Order ID",
        "Email","Whatsapp","Status","UPI ID","Refund Amount",
        "Mediator name","Delivered SS","Review SS","Review Link"
    ]]

    sheets_service.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range="A1",
        valueInputOption="RAW",
        body={"values": headers}
    ).execute()

    # ---- Header Style ----
    requests = [{
        "repeatCell": {
            "range": {"sheetId": 0,"startRowIndex": 0,"endRowIndex": 1},
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor":{"red":1,"green":0.8,"blue":0.2},
                    "horizontalAlignment":"CENTER",
                    "textFormat":{"fontSize":18,"bold":True}
                }
            },
            "fields":"userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
        }
    }]

    sheets_service.spreadsheets().batchUpdate(
        spreadsheetId=sheet_id,
        body={"requests": requests}
    ).execute()

    permission = {
        "type": "user",
        "role": "writer",
        "emailAddress": "hd-839@last-488313.iam.gserviceaccount.com"   # 👈 Change this
    }

    drive_service.permissions().create(
        fileId=sheet_id,
        body=permission
    ).execute()

    return f"✅ Setup Complete<br><a href='{sheet_url}' target='_blank'>Open Sheet</a>"

# ---------- RUN ----------
if __name__ == "__main__":
    app.run(debug=True)


