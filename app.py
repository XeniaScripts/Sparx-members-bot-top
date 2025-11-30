import os
import requests
import psycopg2
from urllib.parse import urlparse
from datetime import datetime
from flask import Flask, redirect, request, render_template_string

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

# HTML TEMPLATES
LANDING_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sparx Free Members Bot - Authorization</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0a0a1f 0%, #1a0033 50%, #0a0a2e 100%);
            color: #fff;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            position: relative;
            overflow: hidden;
        }

        /* Galaxy Background with Stars */
        .stars {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 0;
        }

        .star {
            position: absolute;
            width: 2px;
            height: 2px;
            background: white;
            border-radius: 50%;
            animation: twinkle 3s infinite;
        }

        @keyframes twinkle {
            0%, 100% { opacity: 0.3; }
            50% { opacity: 1; }
        }

        .container {
            position: relative;
            z-index: 1;
            max-width: 600px;
            width: 90%;
            padding: 40px;
            background: rgba(20, 20, 50, 0.8);
            border-radius: 20px;
            border: 1px solid rgba(100, 50, 200, 0.3);
            backdrop-filter: blur(10px);
            text-align: center;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }

        .logo {
            font-size: 48px;
            margin-bottom: 10px;
        }

        h1 {
            font-size: 32px;
            margin-bottom: 15px;
            background: linear-gradient(135deg, #6366f1, #a78bfa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .subtitle {
            font-size: 16px;
            color: #b0b0ff;
            margin-bottom: 30px;
            line-height: 1.6;
        }

        .features {
            margin: 30px 0;
            text-align: left;
            background: rgba(100, 50, 200, 0.1);
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #6366f1;
        }

        .feature {
            display: flex;
            align-items: center;
            margin: 12px 0;
            font-size: 14px;
        }

        .feature-icon {
            margin-right: 12px;
            font-size: 20px;
        }

        .authorize-btn {
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            color: white;
            border: none;
            padding: 14px 40px;
            font-size: 16px;
            font-weight: 600;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.3s;
            margin-top: 20px;
            display: inline-flex;
            align-items: center;
            gap: 10px;
        }

        .authorize-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(99, 102, 241, 0.4);
        }

        .authorize-btn:active {
            transform: translateY(0);
        }

        .discord-logo {
            font-size: 20px;
        }

        .footer {
            margin-top: 30px;
            font-size: 12px;
            color: #888;
            border-top: 1px solid rgba(100, 50, 200, 0.2);
            padding-top: 20px;
        }
    </style>
</head>
<body>
    <div class="stars" id="stars"></div>
    
    <div class="container">
        <div class="logo">✨</div>
        <h1>Sparx Free Members Bot</h1>
        <p class="subtitle">Add authorized members to Discord servers instantly with one command</p>
        
        <div class="features">
            <div class="feature">
                <span class="feature-icon">⚡</span>
                <span>One-click authorization with Discord</span>
            </div>
            <div class="feature">
                <span class="feature-icon">👥</span>
                <span>Bulk add members to any server</span>
            </div>
            <div class="feature">
                <span class="feature-icon">🔒</span>
                <span>Permanent access - tokens never expire</span>
            </div>
            <div class="feature">
                <span class="feature-icon">⚙️</span>
                <span>Use /join [server_id] to add members</span>
            </div>
        </div>

        <form action="/authorize" method="GET">
            <button type="submit" class="authorize-btn">
                <span class="discord-logo">💜</span>
                Authorize with Discord
            </button>
        </form>

        <div class="footer">
            <p>Safe • Secure • No data stored except your Discord ID and tokens</p>
        </div>
    </div>

    <script>
        // Generate random stars
        const starsContainer = document.getElementById('stars');
        for (let i = 0; i < 100; i++) {
            const star = document.createElement('div');
            star.className = 'star';
            star.style.left = Math.random() * 100 + '%';
            star.style.top = Math.random() * 100 + '%';
            star.style.animationDelay = Math.random() * 3 + 's';
            starsContainer.appendChild(star);
        }
    </script>
</body>
</html>
"""

SUCCESS_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Authorization Successful!</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0a0a1f 0%, #1a0033 50%, #0a0a2e 100%);
            color: #fff;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            position: relative;
            overflow: hidden;
        }

        .stars {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 0;
        }

        .star {
            position: absolute;
            width: 2px;
            height: 2px;
            background: white;
            border-radius: 50%;
            animation: twinkle 3s infinite;
        }

        @keyframes twinkle {
            0%, 100% { opacity: 0.3; }
            50% { opacity: 1; }
        }

        .container {
            position: relative;
            z-index: 1;
            max-width: 600px;
            width: 90%;
            padding: 60px 40px;
            background: rgba(20, 20, 50, 0.8);
            border-radius: 20px;
            border: 2px solid #22c55e;
            backdrop-filter: blur(10px);
            text-align: center;
            box-shadow: 0 8px 32px rgba(34, 197, 94, 0.3);
            animation: slideIn 0.5s ease-out;
        }

        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(-20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .icon {
            font-size: 80px;
            margin-bottom: 20px;
            animation: bounce 1s ease-in-out infinite;
        }

        @keyframes bounce {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-10px); }
        }

        h1 {
            font-size: 48px;
            color: #22c55e;
            margin-bottom: 15px;
        }

        .subtitle {
            font-size: 20px;
            color: #b0b0ff;
            margin-bottom: 10px;
        }

        .message {
            font-size: 16px;
            color: #90ee90;
            margin-top: 20px;
            padding: 20px;
            background: rgba(34, 197, 94, 0.1);
            border-left: 4px solid #22c55e;
            border-radius: 5px;
        }

        .instructions {
            margin-top: 30px;
            text-align: left;
            background: rgba(100, 50, 200, 0.1);
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #6366f1;
            font-size: 14px;
            line-height: 1.8;
        }

        .footer {
            margin-top: 30px;
            font-size: 12px;
            color: #888;
        }
    </style>
</head>
<body>
    <div class="stars" id="stars"></div>
    
    <div class="container">
        <div class="icon">✅</div>
        <h1>Authorization Successful!</h1>
        <p class="subtitle">You have been authorised successfully</p>
        
        <div class="message">
            ✨ You may now use the bot to join servers!
        </div>

        <div class="instructions">
            <strong>Next Steps:</strong>
            <br><br>
            1. Use the command: <code style="background: rgba(0,0,0,0.3); padding: 5px 10px; border-radius: 3px;">/join [server_id]</code>
            <br><br>
            2. Replace [server_id] with the Discord server ID where you want to add members
            <br><br>
            3. All authorized members will be added to that server instantly!
        </div>

        <div class="footer">
            <p>🎉 Your authorization is permanent and will never expire</p>
        </div>
    </div>

    <script>
        const starsContainer = document.getElementById('stars');
        for (let i = 0; i < 100; i++) {
            const star = document.createElement('div');
            star.className = 'star';
            star.style.left = Math.random() * 100 + '%';
            star.style.top = Math.random() * 100 + '%';
            star.style.animationDelay = Math.random() * 3 + 's';
            starsContainer.appendChild(star);
        }
    </script>
</body>
</html>
"""

ERROR_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Authorization Failed</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0a0a1f 0%, #1a0033 50%, #0a0a2e 100%);
            color: #fff;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            position: relative;
            overflow: hidden;
        }

        .stars {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 0;
        }

        .star {
            position: absolute;
            width: 2px;
            height: 2px;
            background: white;
            border-radius: 50%;
            animation: twinkle 3s infinite;
        }

        @keyframes twinkle {
            0%, 100% { opacity: 0.3; }
            50% { opacity: 1; }
        }

        .container {
            position: relative;
            z-index: 1;
            max-width: 600px;
            width: 90%;
            padding: 60px 40px;
            background: rgba(20, 20, 50, 0.8);
            border-radius: 20px;
            border: 2px solid #ef4444;
            backdrop-filter: blur(10px);
            text-align: center;
            box-shadow: 0 8px 32px rgba(239, 68, 68, 0.3);
        }

        .icon {
            font-size: 80px;
            margin-bottom: 20px;
        }

        h1 {
            font-size: 48px;
            color: #ef4444;
            margin-bottom: 15px;
        }

        .error-message {
            font-size: 16px;
            color: #ff6b6b;
            margin-top: 20px;
            padding: 20px;
            background: rgba(239, 68, 68, 0.1);
            border-left: 4px solid #ef4444;
            border-radius: 5px;
        }

        .retry-btn {
            background: linear-gradient(135deg, #ef4444, #dc2626);
            color: white;
            border: none;
            padding: 12px 30px;
            font-size: 16px;
            font-weight: 600;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.3s;
            margin-top: 20px;
            text-decoration: none;
            display: inline-block;
        }

        .retry-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(239, 68, 68, 0.4);
        }

        .footer {
            margin-top: 30px;
            font-size: 12px;
            color: #888;
        }
    </style>
</head>
<body>
    <div class="stars" id="stars"></div>
    
    <div class="container">
        <div class="icon">❌</div>
        <h1>Authorization Failed</h1>
        
        <div class="error-message">
            {{ error_message }}
        </div>

        <a href="/" class="retry-btn">Try Again</a>

        <div class="footer">
            <p>If the problem persists, make sure you're using a valid Discord account</p>
        </div>
    </div>

    <script>
        const starsContainer = document.getElementById('stars');
        for (let i = 0; i < 100; i++) {
            const star = document.createElement('div');
            star.className = 'star';
            star.style.left = Math.random() * 100 + '%';
            star.style.top = Math.random() * 100 + '%';
            star.style.animationDelay = Math.random() * 3 + 's';
            starsContainer.appendChild(star);
        }
    </script>
</body>
</html>
"""

# ROUTES
@app.route('/')
def index():
    return render_template_string(LANDING_PAGE)

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
        return render_template_string(ERROR_PAGE, error_message="No authorization code received"), 400
    
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
            return render_template_string(ERROR_PAGE, error_message=f"Token Error: {error}"), 400
        
        access_token = token_data['access_token']
        refresh_token = token_data.get('refresh_token')
    except Exception as e:
        return render_template_string(ERROR_PAGE, error_message=f"Error getting token: {e}"), 500
    
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
            return render_template_string(ERROR_PAGE, error_message="Could not get user ID"), 500
    except Exception as e:
        return render_template_string(ERROR_PAGE, error_message=f"Error getting user info: {e}"), 500

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
        return render_template_string(ERROR_PAGE, error_message=f"Database Error: {e}"), 500

    return render_template_string(SUCCESS_PAGE)

if __name__ == "__main__":
    init_db()
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
