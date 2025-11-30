from flask import Flask, redirect, request, session
import os
import requests
import json # Used for easy handling of JSON data from Discord

app = Flask(__name__)
# This secret key is needed for Flask sessions. Vercel environment variable is best.
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'a_temporary_dev_secret') 

# --- Discord OAuth2 Configuration (Reads from Vercel Environment Variables) ---
# THESE MUST BE SET IN VERCEl: CLIENT_ID, CLIENT_SECRET, REDIRECT_URI
CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
REDIRECT_URI = os.environ.get("REDIRECT_URI") 

# Permissions needed: identify (know user) and guilds.join (can add user to server)
SCOPES = "identify guilds.join"

# --- 1. /authorize route (The link users click) ---
@app.route('/authorize')
def authorize():
    """Builds the Discord authorization URL and redirects the user to Discord's official page."""
    
    if not CLIENT_ID or not REDIRECT_URI:
        # Failsafe if you forget to set the Vercel variables
        return "Error: Discord Client ID or Redirect URI not configured in Vercel.", 500

    discord_auth_url = (
        f"https://discord.com/oauth2/authorize?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&scope={SCOPES}"
        f"&redirect_uri={REDIRECT_URI}"
    )
    # Redirects the user's browser to the Discord authorization page
    return redirect(discord_auth_url)

# --- 2. /callback route (Discord sends the user back here) ---
@app.route('/callback')
def callback():
    """Receives the authorization code and exchanges it for the user's permanent Access Token."""
    
    code = request.args.get('code')
    
    if not code:
        # If the user clicks 'Cancel' on the Discord authorization page
        return "Authorization failed or denied by the user."
        
    # Step 1: Prepare the data to exchange the 'code' for the permanent Access Token
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
    
    # This is the critical step: saving the data. 
    # **In a real bot, you would connect to a database here** (like SQLite)
    # and save token_data['access_token'] and token_data['refresh_token']
    # to be used by your Katabump bot later when a user types /join.

    # For this simple example, we just show a success message:
    return (
        "<h2>✅ Authorization Successful!</h2>"
        "<p>Your access token was retrieved by the server. Your bot on Katabump now has the permission to add you.</p>"
        "<p>You may now return to Discord and use the <code>/join</code> command.</p>"
    )

# --- Simple Root Route ---
@app.route('/')
def index():
    return "This is the Vercel server for Discord OAuth2. Please use the /authorize link found in Discord."

if __name__ == '__main__':
    # This is only for local testing, Vercel handles the production launch
    app.run(port=5000)
