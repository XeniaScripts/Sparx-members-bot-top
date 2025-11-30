import os
import requests
import psycopg2
from urllib.parse import urlparse
from datetime import datetime
from flask import Flask, redirect, request

# --- CONFIGURATION ---
CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
REDIRECT_URI = os.environ.get("REDIRECT_URI") 

# FINAL FIX: Explicitly reads the DATABASE_URL variable
DB_URL = os.environ.get("DATABASE_URL") 
SCOPES = "identify guilds.join"

# Initialize Flask App
app = Flask(__name__)
# Vercel requires a secret key for session security
app.secret_key = os.environ.get('FLASK_SECRET_KEY', os.urandom(24))

# --- Database Helper Function ---
def connect_to_db():
    """Connects to the remote PostgreSQL database using the DATABASE_URL variable."""
    if not DB_URL:
        raise ValueError("DATABASE_URL not found in environment variables.")
    
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

# --- 1. Root Route for Health Check ---
@app.route('/')
def index():
    return "The Discord OAuth2 Vercel Server is running."

# --- 2. /authorize route ---
@app.route('/authorize')
def authorize():
    if not CLIENT_ID or not REDIRECT_URI:
        return "Error: Discord Client ID or Redirect URI not configured.", 500

    discord_auth_url = (
        f"https://discord.com/oauth2/authorize?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&scope={SCOPES}"
        f"&redirect_uri={REDIRECT_URI}"
    )
    return redirect(discord_auth_url)

# --- 3. /callback route (SAVES DATA TO POSTGRES) ---
@app.route('/callback')
def callback():
    code = request.args.get('code')
    
    if not code:
        return "Authorization failed or denied by the user."
        
    # Step 1: Exchange code for token
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
    token_req = requests.post(token_url, data=data, headers=headers)
    token_data = token_req.json()

    if 'access_token' not in token_data:
        return f"Error exchanging code for token: {token_data.get('error_description', 'Unknown error')}", 400

    # Step 2: Extract tokens and user ID
    access_token = token_data['access_token']
    
    user_req = requests.get('https://discord.com/api/v10/users/@me', 
                            headers={'Authorization': f'Bearer {access_token}'})
    user_data = user_req.json()
    user_id = user_data.get('id')
    
    if not user_id:
        return "Error: Could not retrieve user ID after authorization.", 500

    # Step 3: Save/update the user's token data in the PostgreSQL database
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
        """, (user_id, access_token, token_data.get('refresh_token'), datetime.now()))
        
        conn.commit()
        conn.close()
    except Exception as e:
        return f"Database Save Failed: {e}", 500

    return (
        "<h2>✅ Authorization Successful!</h2>"
        "<p>Your permission has been saved to the remote database. You may now return to Discord and use the <code>/join</code> command.</p>"
    )
