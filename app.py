from flask import Flask, redirect, request, session
import os
import requests
import json 

app = Flask(__name__)

# IMPORTANT: This must be set as an Environment Variable in Vercel.
app.secret_key = os.environ['FLASK_SECRET_KEY'] 

# --- Discord OAuth2 Configuration ---
CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
REDIRECT_URI = os.environ.get("REDIRECT_URI") 
SCOPES = "identify guilds.join"

# --- 1. /authorize route ---
@app.route('/authorize')
def authorize():
    """Builds the Discord authorization URL and redirects the user."""
    
    if not CLIENT_ID or not REDIRECT_URI:
        return "Error: Discord Client ID or Redirect URI not configured in Vercel.", 500

    discord_auth_url = (
        f"https://discord.com/oauth2/authorize?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&scope={SCOPES}"
        f"&redirect_uri={REDIRECT_URI}"
    )
    return redirect(discord_auth_url)

# --- 2. /callback route (Database WRITEING CODE IS REMOVED HERE) ---
@app.route('/callback')
def callback():
    """Receives the authorization code and exchanges it for the user's permanent Access Token."""
    
    code = request.args.get('code')
    
    if not code:
        return "Authorization failed or denied by the user."
        
    # Step 1: Prepare data for token exchange
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'scope': SCOPES
    }
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    # Step 2: Send the POST request to Discord's API
    r = requests.post('https://discord.com/api/oauth2/token', data=data, headers=headers)
    token_data = r.json()

    if 'access_token' not in token_data:
        return f"Error exchanging code for token: {token_data.get('error_description', 'Unknown error')}", 400
    
    # --- SUCCESS - Token Received, Database Save Step SKIPPED ---
    
    return (
        "<h2>✅ Authorization Successful! (Token Verified)</h2>"
        "<p>Your access token was successfully retrieved, confirming all tokens and links are correct. </p>"
        "<p>The final step requires connecting a **Remote Database** service to save this permission.</p>"
    )

# --- Simple Root Route ---
@app.route('/')
def index():
    return "This is the Vercel server for Discord OAuth2. Please use the /authorize link found in Discord."

if __name__ == '__main__':
    app.run(port=5000)
