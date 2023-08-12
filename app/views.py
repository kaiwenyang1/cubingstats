from flask import render_template, jsonify, request
from . import app, mysql
from .competitor import get_user_name_mapping

RECORDS_PER_PAGE = 20

@app.route('/rankings/<string:event_id>', methods=['POST', 'GET'])
def rankings(event_id):
    page = int(request.args.get('page', 1))

    cur = mysql.connection.cursor()

    selected_event = "333"

    cur.execute("SELECT DISTINCT eventId FROM Results")
    events = [item[0] for item in cur.fetchall()]

    if request.method == 'POST':
        previous_event = selected_event
        selected_event = request.form.get('selected_event')

        page = int(request.form.get('page'))
    
    offset = (page - 1) * 100
    cur.execute("SELECT * FROM RanksSingle WHERE eventId = %s LIMIT 100 OFFSET %s", (selected_event, offset))
    raw_results = cur.fetchall()
    column_names = [column[0] for column in cur.description]

    # Convert raw_results to a list of dictionaries
    stats = [dict(zip(column_names, row)) for row in raw_results]

    # Calculate number of pages
    cur.execute("SELECT * FROM RanksSingle WHERE eventId = %s", (selected_event,))

    user_names = get_user_name_mapping()



    raw_results = cur.fetchall()
    total_records = len(raw_results)

    print(total_records)
    total_pages = -(-total_records // 100) 

    return render_template('rankings.html', page = page, total_pages = total_pages, user_names = user_names,
        events = events, stats=stats, event_id=event_id, selected_event = selected_event)

@app.route('/person/<string:user_id>', methods=['POST', 'GET'])  # Updated to use <string:user_id>
def person_stats(user_id):
    cur = mysql.connection.cursor()
    selected_event = "333"
    
    # default event is 3x3x3

    cur.execute("SELECT * FROM Persons WHERE id = %s", [user_id])
    raw_results = cur.fetchall()
    person_name = raw_results[0][2]
    # fetch the user's actual name

    cur.execute("SELECT DISTINCT eventId FROM Results WHERE personId = %s" , [user_id])
    events = [item[0] for item in cur.fetchall()]
    # fetch the list of events user has participated in before

    if request.method == 'POST':
        selected_event = request.form.get('event_name')
    
    cur.execute("SELECT * FROM Results WHERE personId = %s AND eventId = %s", (user_id, selected_event))
    raw_results = cur.fetchall()
    column_names = [column[0] for column in cur.description]
    # Convert raw_results to a list of dictionaries

    stats = [dict(zip(column_names, row)) for row in raw_results]
    # fetch results in selected event
        
    return render_template('person_stats.html', selected_event = selected_event, events=events, results=stats,
        name=person_name, user_id = user_id)

@app.route('/search', methods=['POST', 'GET'])
def search():
    search_name = request.form.get('name') or request.args.get('name', '')
    page = int(request.args.get('page', 1))

    offset = (page - 1) * RECORDS_PER_PAGE

    cur = mysql.connection.cursor()

    # count total records
    total_query = "SELECT COUNT(*) FROM Persons WHERE name LIKE %s"
    params = ("%" + search_name + "%",)
    cur.execute(total_query, params)
    total_results = cur.fetchone()[0]
    total_pages = -(-total_results // RECORDS_PER_PAGE)

    # fetch records
    query = "SELECT * FROM Persons WHERE name LIKE %s LIMIT %s OFFSET %s"
    cur.execute(query, (params[0], RECORDS_PER_PAGE, offset))
    raw_results = cur.fetchall()
    column_names = [column[0] for column in cur.description]

    # convert raw results to a list of dictionaries to use
    stats = [dict(zip(column_names, row)) for row in raw_results]

    return render_template('index.html', stats=stats, page=page, total_pages=total_pages, search_name=search_name)

@app.route('/')
def index():
    return render_template('index.html')
