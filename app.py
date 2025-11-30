from flask import Flask, redirect, request, session
import os
import requests
import json 

app = Flask(__name__)

# IMPORTANT: This must be set as an Environment Variable in Vercel for security.
# It will crash if not set, which is safer than using a default key.
app.secret_key = os.environ['FLASK_SECRET_KEY'] 

# --- Discord OAuth2 Configuration (Reads from Vercel Environment Variables) ---
CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
REDIRECT_URI = os.environ.get("REDIRECT_URI") 

SCOPES = "identify guilds.join"

# --- 1. /authorize route (The link users click) ---
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

# --- 2. /callback route (Discord sends the user back here) ---
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
    
    # --- SUCCESS ---
    # In a real bot, you would save this token data to a database now!
    
    return (
        "<h2>✅ Authorization Successful!</h2>"
        "<p>Your access token was retrieved by the server. Your bot now has the permission to add you.</p>"
        "<p>You may now return to Discord and use the <code>/join</code> command.</p>"
    )

# --- Simple Root Route ---
@app.route('/')
def index():
    return "This is the Vercel server for Discord OAuth2. Please use the /authorize link found in Discord."

if __name__ == '__main__':
    # Vercel handles the production launch, but this is for local testing
    app.run(port=5000)
