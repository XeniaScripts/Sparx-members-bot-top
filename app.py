from flask import Flask, redirect, request
import os
import requests
import psycopg2
from urllib.parse import urlparse
from datetime import datetime

app = Flask(__name__)

# --- CONFIGURATION ---
app.secret_key = os.environ['FLASK_SECRET_KEY'] 
CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
REDIRECT_URI = os.environ.get("REDIRECT_URI") 
DB_URL = os.environ.get("DATABASE_URL") # Reads the Vercel/Neon URL
SCOPES = "identify guilds.join"

# --- Database Helper Function ---
def connect_to_db():
    """Connects to the remote PostgreSQL database."""
    if not DB_URL:
        # Vercel provides this automatically via integration, so this is a safety check.
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

# --- 1. /authorize route (remains the same) ---
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

# --- 2. /callback route (SAVES DATA TO POSTGRES) ---
@app.route('/callback')
def callback():
    code = request.args.get('code')
    if not code:
        return "Authorization failed or denied by the user."
        
    # 1. Exchange code for token (requests.post logic)
    # ... (code for token exchange here) ...

    # 2. Extract tokens and user ID
    access_token = token_data.get('access_token')
    refresh_token = token_data.get('refresh_token')
    
    user_req = requests.get('https://discord.com/api/v10/users/@me', 
                            headers={'Authorization': f'Bearer {access_token}'})
    user_data = user_req.json()
    user_id = user_data.get('id')
    
    if not user_id:
        return "Error: Could not retrieve user ID after authorization.", 500

    # 3. Save/update the user's token data in the PostgreSQL database
    try:
        conn = connect_to_db()
        cursor = conn.cursor()
        
        # INSERT OR REPLACE handles existing users
        cursor.execute("""
            INSERT INTO authorized_users 
            (user_id, access_token, refresh_token, timestamp) 
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE SET 
            access_token = EXCLUDED.access_token, 
            refresh_token = EXCLUDED.refresh_token,
            timestamp = EXCLUDED.timestamp
        """, (user_id, access_token, refresh_token, datetime.now()))
        
        conn.commit()
        conn.close()
    except Exception as e:
        return f"Database Save Failed: {e}", 500

    return (
        "<h2>✅ Authorization Successful!</h2>"
        "<p>Your permission has been saved to the remote database. You may now return to Discord and use the <code>/join</code> command.</p>"
    )

@app.route('/')
def index():
    return "This is the Vercel server for Discord OAuth2."

if __name__ == '__main__':
    app.run(port=5000)
