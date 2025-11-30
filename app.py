# ... (imports and configuration setup remain the same) ...
import sqlite3 # Added for database functionality

# New: Database path must be the same as the one used in main.py
DB_PATH = os.environ.get('DB_PATH', 'auth_data.db') 

# --- Database Helper Function ---
def init_db():
    """Initializes the database table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS authorized_users (
            user_id TEXT PRIMARY KEY,
            access_token TEXT NOT NULL,
            refresh_token TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()

# Initialize the database when the web server starts
init_db()

# ... (authorize route remains the same) ...

# --- /callback route (Discord sends the user back here) ---
@app.route('/callback')
def callback():
    # ... (code to exchange code for token remains the same) ...
    # ... (token_data is successfully retrieved) ...

    # --- SUCCESS - SAVE DATA TO DATABASE ---
    
    access_token = token_data['access_token']
    refresh_token = token_data.get('refresh_token')
    
    # We need to find out the user's ID
    user_req = requests.get('https://discord.com/api/v10/users/@me', 
                            headers={'Authorization': f'Bearer {access_token}'})
    user_data = user_req.json()
    user_id = user_data.get('id')
    
    if not user_id:
        return "Error: Could not retrieve user ID after authorization.", 500

    # Save/update the user's token data in the database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT OR REPLACE INTO authorized_users 
        (user_id, access_token, refresh_token, timestamp) 
        VALUES (?, ?, ?, datetime('now'))
    """, (user_id, access_token, refresh_token))
    
    conn.commit()
    conn.close()

    return (
        "<h2>✅ Authorization Successful!</h2>"
        "<p>Your permission has been saved. You may now return to Discord and use the <code>/join</code> command.</p>"
    )

# ... (index route remains the same) ...
