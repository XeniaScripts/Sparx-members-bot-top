import os
import requests
import psycopg2
from urllib.parse import urlparse
from datetime import datetime
from flask import Flask, redirect, request

CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
REDIRECT_URI = os.environ.get("REDIRECT_URI") 
DB_URL = os.environ.get("DATABASE_URL") 
SCOPES = "identify guilds guilds.join"

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', os.urandom(24))

def connect_to_db():
    if not DB_URL:
        raise ValueError("DATABASE_URL not found")
    url = urlparse(DB_URL)
    conn = psycopg2.connect(
        database=url.path[1:],
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port,
        sslmode='require' 
    )
    return conn

def init_db():
    try:
        conn = connect_to_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS authorized_users (
                user_id TEXT PRIMARY KEY,
                access_token TEXT NOT NULL,
                refresh_token TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            ALTER TABLE authorized_users
            ADD COLUMN IF NOT EXISTS refresh_token TEXT
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        print("✅ Database initialized", flush=True)
    except Exception as e:
        print(f"🚨 Database init error: {e}", flush=True)

@app.route('/')
def index():
    return "Discord OAuth2 Server is running."

@app.route('/authorize')
def authorize():
    if not CLIENT_ID or not REDIRECT_URI:
        return "Error: Missing CLIENT_ID or REDIRECT_URI", 500
    discord_auth_url = (
        f"https://discord.com/oauth2/authorize"
        f"?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&scope={SCOPES}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&prompt=consent"
    )
    return redirect(discord_auth_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    if not code:
        return "Authorization failed.", 400
    
    token_url = 'https://discord.com/api/v10/oauth2/token'
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'scope': SCOPES
    }
    
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    
    try:
        token_req = requests.post(token_url, data=data, headers=headers, timeout=5)
        token_data = token_req.json()
        
        if 'access_token' not in token_data:
            error = token_data.get('error_description', 'Unknown error')
            return f"Token Error: {error}", 400
        
        access_token = token_data['access_token']
        refresh_token = token_data.get('refresh_token')
    except Exception as e:
        return f"Error getting token: {e}", 500
    
    try:
        user_req = requests.get(
            'https://discord.com/api/v10/users/@me',
            headers={'Authorization': f'Bearer {access_token}'},
            timeout=5
        )
        user_data = user_req.json()
        user_id = user_data.get('id')
        username = user_data.get('username', 'Unknown')
        
        if not user_id:
            return "Could not get user ID", 500
    except Exception as e:
        return f"Error getting user info: {e}", 500

    try:
        conn = connect_to_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO authorized_users 
            (user_id, access_token, refresh_token, timestamp) 
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE SET 
            access_token = EXCLUDED.access_token, 
            refresh_token = EXCLUDED.refresh_token,
            timestamp = EXCLUDED.timestamp
        """, (str(user_id), access_token, refresh_token, datetime.now()))
        
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        return f"Database Error: {e}", 500

    return (
        f"<h2>✅ Authorized!</h2>"
        f"<p>User: <b>{username}</b></p>"
        f"<p>You have been authorised successfully</p>"
        f"<p>You may now use the bot to join servers!</p>"
    )

if __name__ == "__main__":
    init_db()
    app.run(debug=False)
