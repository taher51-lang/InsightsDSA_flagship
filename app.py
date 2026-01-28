from flask import Flask, render_template, request, jsonify,session,redirect,url_for
import psycopg2.extras
import psycopg2
from dotenv import load_dotenv
import os
load_dotenv()
app = Flask(__name__)
@app.route("/")
def LoginPage():
    return render_template("login.html")
app.secret_key = os.getenv("FLASK_SECRET_KEY") # Use a strong key

def getDBConnection():
    # Pulling DB details from .env for security
    con = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS")
    )
    return con
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    userpass = data.get("userpass")
    con = getDBConnection()
    # CHANGE 1: Added the factory so the database returns a Dictionary instead of a Tuple
    cur = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    # Good practice: explicitly select the columns you need instead of '*'
    cur.execute("SELECT id, username, name FROM users WHERE username = %s AND userpassword = %s", (username, userpass))
    result = cur.fetchone()
    if result:
        # This now works perfectly because 'result' is a dictionary
        session['user_id'] = result['id'] 
        session['username'] = result['username']    
        # CHANGE 2: Always close connections before returning
        cur.close()
        con.close()
        print(result['name'])
        # Added redirect URL so your JS knows where to send the user
        return jsonify({"message": "Login successful","name":result['name']}), 200
    else:
        # Close connections here too
        cur.close()
        con.close()
        return jsonify({"message": "Invalid Credentials"}), 401

@app.route("/register_page")
def register_page():
    return render_template("register.html")

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    userpass = data.get("userpass")
    con = getDBConnection()
    cur = con.cursor()
    print("Hello")
    # FIX: Added the comma (username,) to make it a proper Tuple
    cur.execute("SELECT * FROM users WHERE userName = %s", (username,))
    result = cur.fetchone()
    if result:
        cur.close()
        con.close()
        return jsonify({"message": "User already exists. Select different username"}), 409
    else:
        query = "INSERT INTO users (username, userpassword) VALUES (%s, %s)"
        cur.execute(query, (username, userpass))
        con.commit() 
        cur.close()
        con.close()
        return jsonify({"message": "User registered successfully!"}), 201
    

@app.route("/dashboard")
def dashboard():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    # Only fetch the basic Concept boxes here for Jinja to loop through
    con = getDBConnection()
    cur = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM concepts") # Your scrollable boxes
    concepts = cur.fetchall()
    cur.close()
    con.close()

    return render_template("dashboard.html", concepts=concepts)
@app.route("/api/user_stats")
def get_user_stats():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    con = getDBConnection()
    cur = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # Query 1: Total Solved
    cur.execute("SELECT COUNT(*) as solved_count FROM user_progress WHERE user_id = %s", (user_id,))
    total_solved = cur.fetchone()['solved_count']
    
    # Query 2: Active Days
    cur.execute("SELECT COUNT(DISTINCT TO_CHAR(solved_at, 'YYYY-MM-DD')) as streak FROM user_progress WHERE user_id = %s", (user_id,))
    streak = cur.fetchone()['streak']

    cur.close()
    con.close()
    print(total_solved)
    print(streak)
    print("hello")
    return jsonify({
        "total_solved": total_solved,
        "streak": streak
    })
@app.route("/questions/<int:concept_id>")
def questions_page(concept_id):
    # This just renders the blank page with the concept_id passed to the template
    return render_template("questions.html", concept_id=concept_id)
@app.route("/api/get_questions/<int:concept_id>")
def get_questions_api(concept_id):
    user_id = session.get('user_id')
    con = getDBConnection()
    cur = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # Query: Get all questions for this concept AND check if THIS user solved them
    query = """
        SELECT q.id, q.title, q.difficulty, q.link,
               CASE WHEN up.question_id IS NOT NULL THEN TRUE ELSE FALSE END as is_solved
        FROM questions q
        LEFT JOIN user_progress up ON q.id = up.question_id AND up.user_id = %s
        WHERE q.concept_id = %s
    """
    cur.execute(query, (user_id, concept_id))
    questions = cur.fetchall()
    print(questions)
    print("Hello")
    cur.close()
    con.close()
    return jsonify(questions)
@app.route("/api/get_question_details/<int:q_id>")
def get_question_details(q_id):
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    con = getDBConnection()
    # Use RealDictCursor to access columns by name (e.g., row['title'])
    cur = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    try:
        # SQL Logic: Get the Title, Description, and calculate 'is_solved'
        # If the user_progress row exists, 'is_solved' becomes TRUE.
        query = """
            SELECT q.id, q.title, q.description, q.difficulty, q.link,
                   CASE WHEN up.question_id IS NOT NULL THEN TRUE ELSE FALSE END as is_solved
            FROM questions q
            LEFT JOIN user_progress up ON q.id = up.question_id AND up.user_id = %s
            WHERE q.id = %s
        """
        cur.execute(query, (user_id, q_id))
        data = cur.fetchone()
        
        if not data:
            return jsonify({"error": "Question not found"}), 404
            
        return jsonify(data)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        con.close()
@app.route("/api/toggle_solve", methods=["POST"])
def toggle_solve():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json()
    q_id = data.get("question_id")
    
    con = getDBConnection()
    cur = con.cursor()
    
    try:
        # 1. Check if the user has already solved this specific question
        cur.execute("SELECT 1 FROM user_progress WHERE user_id = %s AND question_id = %s", (user_id, q_id))
        exists = cur.fetchone()
        
        if exists:
            # 2. Logic: If it exists, DELETE it (Reset Progress)
            cur.execute("DELETE FROM user_progress WHERE user_id = %s AND question_id = %s", (user_id, q_id))
            action = "reset"
        else:
            # 3. Logic: If it doesn't exist, INSERT it (Mark as Done)
            cur.execute("INSERT INTO user_progress (user_id, question_id) VALUES (%s, %s)", (user_id, q_id))
            action = "solved"
            
        con.commit() # IMPORTANT: Save changes to the database
        return jsonify({"status": "success", "action": action})
        
    except Exception as e:
        con.rollback() # Undo changes if something crashes
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        con.close()
if __name__ == "__main__":
    app.run(debug=True)