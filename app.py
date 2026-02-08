from flask import Flask, render_template, request, jsonify,session,redirect,url_for
from aiBotBackend import chatbot;
from datetime import date, timedelta 
import psycopg2.extras
import psycopg2
from dotenv import load_dotenv
import os
load_dotenv()
app = Flask(__name__)
def sm2_algorithm(quality, current_interval, current_ease, repetitions):
    """
    Inputs:
        quality: 0 (Forgot), 3 (Hard), 4 (Good), 5 (Easy)
        current_interval: Days since last review
        current_ease: Difficulty multiplier (default 2.5)
        repetitions: How many times successfully reviewed in a row
    
    Returns:
        (new_interval, new_ease, new_repetitions, next_review_date)
    """
    # 1. HANDLE "FORGOT" (Reset Logic)
    if quality < 3:
        new_reps = 0
        new_interval = 1  # Reset to 1 day (Review tomorrow)
        new_ease = current_ease # Keep ease factor same (or could decrease it)
        
    # 2. HANDLE SUCCESS (Growth Logic)
    else:
        new_reps = repetitions + 1
        
        # Standard SM-2 Intervals
        if new_reps == 1:
            new_interval = 1
        elif new_reps == 2:
            new_interval = 6
        else:
            # The Magic Formula: Previous Interval * Ease Factor
            new_interval = int(current_interval * current_ease)

        # Update Ease Factor (Math to adjust difficulty)
        # If user found it hard, Ease Factor drops. If easy, it rises.
        new_ease = current_ease + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        
        # Cap the Ease Factor (Don't let it get too low, or intervals will never grow)
        if new_ease < 1.3:
            new_ease = 1.3

    # 3. CALCULATE DATE
    next_review_date = date.today() + timedelta(days=new_interval)

    return new_interval, new_ease, new_reps, next_review_date
@app.route("/")
def homePage():
    return render_template("landing.html")
@app.route("/loginpage")
def LoginPage():
    return render_template("regAndLogin.html")
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
    # print(username)
    # print(userpass)
    # print(result)
    if result:
        # This now works perfectly because 'result' is a dictionary
        session['user_id'] = result['id'] 
        session['username'] = result['username']    
        # CHANGE 2: Always close connections before returning
        cur.close()
        con.close()
        print(result['name'])
        return jsonify({"message": "Login successful","name":result['name']}), 200
    else:
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
    print("Hellothisisregistercheck")
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
        cur.execute("SELECT id FROM users WHERE username = %s AND userpassword = %s", (username, userpass))
        result = cur.fetchone()
        session['user_id'] = result[0] 
        session['username'] = username 
        con.commit() 
        cur.close()
        con.close()
        return jsonify({"message": "User registered successfully!"}), 201
    

@app.route("/dashboard")
def dashboard():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    con = getDBConnection()
    # You are using RealDictCursor, so results are dicts {'col_name': value}
    cur = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # 1. Fetch Concepts
    cur.execute("SELECT * FROM concepts") 
    concepts = cur.fetchall()

    # 2. Fetch Stats (Give aliases to your aggregates!)
    cur.execute("""
        SELECT 
            AVG(ease_factor) as avg_ease, 
            MIN(next_review) as next_date
        FROM user_progress 
        WHERE user_id = %s AND is_solved = TRUE
    """, (user_id,))
    
    rev_stats = cur.fetchone()

    # FIX: Access by Key Name, not Index [0]
    if rev_stats and rev_stats['avg_ease']:
        avg_ease = float(rev_stats['avg_ease'])
        next_date = rev_stats['next_date']
    else:
        avg_ease = 2.5
        next_date = None

    # Logic remains the same...
    retention_pct = int(min(100, (avg_ease / 3.0) * 100))

    if next_date:
        delta = (next_date - date.today()).days
        if delta < 0:
            days_label = "Overdue!"
            days_color = "text-danger"
        elif delta == 0:
            days_label = "Due Today"
            days_color = "text-warning"
        else:
            days_label = f"{delta} Days Left"
            days_color = "text-success"
    else:
        days_label = "No Reviews"
        days_color = "text-muted"
    cur.execute("""
        SELECT COUNT(*) as count 
        FROM user_progress 
        WHERE user_id = %s AND "interval" <= 3
    """, (user_id,))
    short_term = cur.fetchone()['count']

    # --- 2. GET STARTING TO STICK (Medium Term) ---
    # Logic: Interval is medium (4-14 days). You know these somewhat well.
    cur.execute("""
        SELECT COUNT(*) as count 
        FROM user_progress 
        WHERE user_id = %s AND "interval" > 3 AND "interval" <= 14
    """, (user_id,))
    medium_term = cur.fetchone()['count']

    # --- 3. GET MASTERED (Long Term) ---
    # Logic: Interval is large (> 14 days). These are solid.
    cur.execute("""
        SELECT COUNT(*) as count 
        FROM user_progress 
        WHERE user_id = %s AND "interval" > 14
    """, (user_id,))
    long_term = cur.fetchone()['count']

    # Package the data for the chart [Short, Medium, Long]
    chart_data = [short_term, medium_term, long_term]
    cur.close()
    con.close()
    print(f"DEBUG CHART DATA: {chart_data}")
    
    return render_template('dashboard.html', 
                           retention_pct=retention_pct,
                           days_label=days_label,
                           days_color=days_color,
                           concepts=concepts,
                           chart_data = chart_data
                           )
    
@app.route("/api/user_stats")
def get_user_stats():
    user_id = session.get('user_id')
    
    con = getDBConnection()
    cur = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # 1. Get Total Solved (Your existing logic is fine here)
    cur.execute("""
        SELECT COUNT(*) as solved_count 
        FROM user_progress 
        WHERE user_id = %s AND is_solved = TRUE
    """, (user_id,))
    total_result = cur.fetchone()
    total_solved = total_result['solved_count'] if total_result else 0
    
    # 2. Get Streak (THE FIX)
    # Fetch all unique dates the user was active, ordered by newest first
    cur.execute("""
        SELECT DISTINCT DATE(solved_at) as activity_date
        FROM user_progress
        WHERE user_id = %s AND solved_at IS NOT NULL
        ORDER BY activity_date DESC
    """, (user_id,))
    
    # Convert list of dicts to a Set of date objects for easy lookup
    rows = cur.fetchall()
    active_dates = {row['activity_date'] for row in rows}
    
    cur.close()
    con.close()

    # --- PYTHON STREAK ALGORITHM ---
    streak = 0
    today = date.today()
    
    # Check if the streak is alive (Active Today OR Yesterday)
    if today in active_dates:
        streak = 1
        check_date = today - timedelta(days=1) # Start checking from Yesterday
    elif (today - timedelta(days=1)) in active_dates:
        streak = 1
        check_date = today - timedelta(days=2) # Start checking from Day Before Yesterday
    else:
        streak = 0 # Streak is broken
        check_date = None

    # Count backwards as long as there is no gap
    while check_date and check_date in active_dates:
        streak += 1
        check_date -= timedelta(days=1)

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
    cur = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
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
        # 1. Check if it exists
        cur.execute("SELECT 1 FROM user_progress WHERE user_id = %s AND question_id = %s", (user_id, q_id))
        exists = cur.fetchone()
        
        if exists:
            # OPTION A: Reset (Delete row)
            cur.execute("DELETE FROM user_progress WHERE user_id = %s AND question_id = %s", (user_id, q_id))
            action = "reset"
            
        else:
            # OPTION B: First Solve (Initialize SRS Defaults)
            tomorrow = date.today() + timedelta(days=1)
            
            # Note the double quotes around "interval" for Postgres!
            query = """
                INSERT INTO user_progress 
                (user_id, question_id, solved_at, "interval", ease_factor, repetitions, next_review, is_solved) 
                VALUES (%s, %s, NOW(), 1, 2.5, 0, %s, TRUE)
            """
            cur.execute(query, (user_id, q_id, tomorrow))
            action = "solved"
            
        con.commit() 
        return jsonify({"status": "success", "action": action})
        
    except Exception as e:
        con.rollback() 
        print(f"Error: {e}") # Good for debugging
        return jsonify({"error": str(e)}), 500
        
    finally:
        cur.close()
        con.close()
@app.route("/api/ask_ai", methods=["POST"])
def ask_AI():
    data = request.get_json()
    con = getDBConnection()
    query = "select description from questions where question_id = "
    question_id = data.get("question_id")
    query = data.get("query")
    thread_id = 1
    config = {"configurable": {"thread_id": thread_id}}
    response = chatbot.invoke({'user_input': query,'question': question_id},config=config)
    return jsonify({"answer": response['bot_response']})

@app.route('/memory')
def memory():
    user_id = session.get('user_id')
    
    con = getDBConnection()
    cur = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    try:
        # --- QUERY 1: FETCH REVIEW QUEUE ---
        # Changed c.name -> c.title
        cur.execute("""
            SELECT 
                q.id as question_id, 
                q.title as question_title, 
                q.link as question_link, 
                c.title as concept_title,   -- <--- FIXED: using c.title
                up."interval" as days_interval
            FROM questions q
            JOIN user_progress up ON q.id = up.question_id
            JOIN concepts c ON q.concept_id = c.id
            WHERE up.user_id = %s AND up.next_review <= CURRENT_DATE
            ORDER BY up.next_review ASC
        """, (user_id,))
        
        review_queue = cur.fetchall()
        
        # --- QUERY 2: FETCH STATS ---
        # Changed c.name -> c.title here too
        cur.execute("""
            SELECT 
                c.title as concept_title,   -- <--- FIXED
                COUNT(up.question_id) as solved_count, 
                COALESCE(AVG(up.ease_factor), 0) as avg_ease
            FROM concepts c
            LEFT JOIN questions q ON c.id = q.concept_id
            LEFT JOIN user_progress up ON q.id = up.question_id AND up.user_id = %s
            GROUP BY c.id, c.title          -- <--- FIXED: Group by title
        """, (user_id,))
        
        stats_raw = cur.fetchall()
        stats = []

        # Process Stats
        for row in stats_raw:
            name = row['concept_title'] 
            solved = row['solved_count']
            ease = float(row['avg_ease'])
            
            if solved == 0: signal = 0
            elif ease >= 2.6: signal = 4
            elif ease >= 2.1: signal = 3
            elif ease >= 1.5: signal = 2
            else: signal = 1
            
            stats.append({"name": name, "solved": solved, "signal": signal})

        return render_template('retention.html', queue=review_queue, stats=stats)

    except Exception as e:
        print(f"Error: {e}")
        return "Database Error", 500
    finally:
        cur.close()
        con.close()

@app.route('/api/review', methods=['POST'])
def api_review():
    # 1. Security Check
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    # 2. Get Data from Frontend
    question_id = request.form.get('question_id')
    quality = int(request.form.get('quality')) # 0, 3, 4, 5

    con = getDBConnection()
    cur = con.cursor()

    try:
        # 3. Fetch Current Stats
        # We need the OLD values to calculate the NEW ones
        cur.execute("""
            SELECT "interval", ease_factor, repetitions 
            FROM user_progress 
            WHERE user_id = %s AND question_id = %s
        """, (user_id, question_id))
        
        record = cur.fetchone()
        
        # Defaults (Safety net if row exists but values are null)
        curr_ivl = record[0] if record and record[0] else 1
        curr_ease = record[1] if record and record[1] else 2.5
        curr_reps = record[2] if record and record[2] else 0

        # 4. Run the Algorithm
        new_ivl, new_ease, new_reps, new_date = sm2_algorithm(quality, curr_ivl, curr_ease, curr_reps)

        # 5. Update Database
        # Note: We update "solved_at" to NOW() because they just reviewed it.
        cur.execute("""
            UPDATE user_progress 
            SET 
                "interval" = %s,
                ease_factor = %s,
                repetitions = %s,
                next_review = %s,
                solved_at = NOW()
            WHERE user_id = %s AND question_id = %s
        """, (new_ivl, new_ease, new_reps, new_date, user_id, question_id))
        
        con.commit()
        return jsonify({"status": "success", "new_date": str(new_date)})

    except Exception as e:
        con.rollback()
        print("Error in SRS update:", e)
        return jsonify({"error": str(e)}), 500
        
    finally:
        cur.close()
        con.close()

@app.route('/api/roadmap-data')
def roadmap_data():
    user_id = session.get('user_id')
    con = getDBConnection()
    cur = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # --- FETCH CONCEPTS & PROGRESS ---
    cur.execute("""
        SELECT 
            c.id, 
            c.title, 
            COUNT(up.question_id) as solved_count
        FROM concepts c
        LEFT JOIN questions q ON c.id = q.concept_id
        LEFT JOIN user_progress up ON q.id = up.question_id 
             AND up.user_id = %s AND up.is_solved = TRUE
        GROUP BY c.id, c.title
        ORDER BY c.id ASC
    """, (user_id,))
    
    concepts = cur.fetchall()
    cur.close()
    con.close()
    
    # Return raw JSON data
    return jsonify(concepts)
@app.route('/roadmap')
def roadmap():
    return render_template('roadmap.html')
if __name__ == "__main__":
    app.secret_key="THERRANGBHRUCH"
    app.run(debug=True)