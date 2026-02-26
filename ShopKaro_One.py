from flask import Flask, render_template, request, redirect, session,url_for
import mysql.connector
import random
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import cloudinary
import cloudinary.uploader
from datetime import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials as SACredentials
import json
import os

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

app = Flask(__name__)
app.secret_key = "heavy-secret"

cloudinary.config(
    cloud_name="dajnnvznf",
    api_key="949949375829316",
    api_secret="BQ1CJTtlscFnilZ1OnU-MBgZ6vA"
)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

clint_secret=json.loads(os.getenv("clint_secret"))
ABCD = json.loads(os.getenv("ABCD"))
creds = ServiceAccountCredentials.from_json_keyfile_dict(ABCD, SCOPES)
client = gspread.authorize(creds)





def db():
    return mysql.connector.connect(
        host="centerbeam.proxy.rlwy.net",
        user="root",
        password="GZFvMhflsqtzEyFBvPOnNtrapaJWNqhF",
        database="railway",
        port=11620
    )

# ---------- HOME ----------
@app.route('/')
def Home():
    return redirect('/login')

@app.route("/login")
def login():

    username = 'shopkaro1'

    # -------- Check Token in DB --------
    conn = db()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT token FROM ShopKaro_mediator
        WHERE username=%s
    """, (username,))

    row = cur.fetchone()
    cur.close()
    conn.close()

    # If token exists → skip Google login
    if row and row["token"]:
        return redirect("/create-sheet")

    # -------- Else Google OAuth --------
    flow = Flow.from_client_secrets_file(
        clint_secret,
        scopes=SCOPES,
        redirect_uri=url_for("callback", _external=True)
    )

    auth_url, state = flow.authorization_url(prompt="consent")
    session["state"] = state

    return redirect(auth_url)


# ---------------- CALLBACK ----------------
@app.route("/callback")
def callback():

    flow = Flow.from_client_secrets_file(
        clint_secret,
        scopes=SCOPES,
        state=session["state"],
        redirect_uri=url_for("callback", _external=True)
    )

    flow.fetch_token(authorization_response=request.url)

    creds = flow.credentials

    # Save token
    token_json = creds.to_json()

    conn = db()
    cur = conn.cursor()
    cur.execute("UPDATE ShopKaro_mediator SET token=%s WHERE username=%s", (token_json,session["Med Username"]))
    conn.commit()
    cur.close()
    conn.close()

    return redirect("/create-sheet")

from google.oauth2.credentials import Credentials
import json

def get_mediator_creds(username):
    conn = db()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT token FROM ShopKaro_mediator
        WHERE username=%s
    """, (username,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row or not row["token"]:
        return None
    
    token_data = json.loads(row["token"])
    creds = Credentials.from_authorized_user_info(token_data)
    return creds

from google.auth.transport.requests import Request

def refresh_if_needed(creds, username):
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        # Save updated token
        conn = db()
        cur = conn.cursor()
        cur.execute("""
            UPDATE ShopKaro_mediator
            SET token=%s
            WHERE username=%s
        """, (
            creds.to_json(),
            username
        ))
        conn.commit()
        cur.close()
        conn.close()
    return creds

# ---------------- CREATE SHEET ----------------
from google.auth.transport.requests import Request

@app.route("/create-sheet")
def create_sheet():

    username = 'shopkaro1'

    creds = get_mediator_creds(username)

    if not creds:
        return redirect("/login")

    creds = refresh_if_needed(creds, username)

    sheets_service = build("sheets", "v4", credentials=creds)
    drive_service = build("drive", "v3", credentials=creds)

    # Continue sheet creation...

    # -------- Create Sheet --------
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

    # -------- Add Header Row --------
    headers = [[
        "TimeStamp",
        "Brand Name",
        "Profile Name",
        "Order Date",
        "Product Name",
        "Order SS",
        "Order Amount",
        "Order ID",
        "Email",
        "Whatsapp",
        "Status",
        "UPI ID",
        "Refund Amount",
        "Mediator name",
        "Delivered SS",
        "Review SS",
        "Review Link"
    ]]

    body = {
        "values": headers
    }

    sheets_service.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range="A1",
        valueInputOption="RAW",
        body=body
    ).execute()

    # -------- Share Sheet --------
    permission = {
        "type": "user",
        "role": "writer",
        "emailAddress": "hd-839@last-488313.iam.gserviceaccount.com"   # 👈 Change this
    }

    drive_service.permissions().create(
        fileId=sheet_id,
        body=permission
    ).execute()

# -------- Format Header Like Screenshot --------

    requests = [

        # Header Style
        {
            "repeatCell": {
                "range": {
                    "sheetId": 0,
                    "startRowIndex": 0,
                    "endRowIndex": 1
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {
                            "red": 1,
                            "green": 0.8,
                            "blue": 0.2
                        },
                        "horizontalAlignment": "CENTER",
                        "verticalAlignment": "MIDDLE",
                        "textFormat": {
                            "fontSize": 18,
                            "bold": True,
                            "foregroundColor": {
                                "red": 0,
                                "green": 0,
                                "blue": 0
                            }
                        }
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"
            }
        },

        # Freeze Header Row
        {
            "updateSheetProperties": {
                "properties": {
                    "sheetId": 0,
                    "gridProperties": {
                        "frozenRowCount": 1
                    }
                },
                "fields": "gridProperties.frozenRowCount"
            }
        },

        # Set Row Height Bigger
        {
            "updateDimensionProperties": {
                "range": {
                    "sheetId": 0,
                    "dimension": "ROWS",
                    "startIndex": 0,
                    "endIndex": 1
                },
                "properties": {
                    "pixelSize": 45
                },
                "fields": "pixelSize"
            }
        }
    ]

    sheets_service.spreadsheets().batchUpdate(
        spreadsheetId=sheet_id,
        body={"requests": requests}
    ).execute()

    
    return f"Compeled Your sheet : {sheet_url}"


# ---------- RUN ----------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)


