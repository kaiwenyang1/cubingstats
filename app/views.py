from flask import render_template, jsonify, request, url_for
from . import app, mysql
from .competitor import get_user_name_mapping

RECORDS_PER_PAGE = 20
event_list = [
"222"
,"333"
,"333bf"
,"333fm"
,"333ft"
,"333mbf"
,"333mbo"
,"333oh"
,"444"
,"444bf"
,"555"
,"555bf"
,"666"
,"777"
,"clock"
,"magic"
,"minx"
,"mmagic"
,"pyram"
,"skewb"
,"sq1"]
blind_events = {"333bf", "333fm", "444bf", "555bf", "333mbf"}
blind_comp_list = set()

def write_to_file(comps_set, filename):
    with open(filename, 'w') as f:
        for comp in comps_set:
            f.write(comp + '\n')

def get_blind_events():

    with open("comp_list.txt", 'r') as f:
        for line in f:

            comp_name, events = line.strip().split('\t')

            events_list = events.split()

            blind_events_count = sum(1 for event in events_list if event in blind_events)

            if blind_events_count * 2 > len(events_list):
                blind_comp_list.add(comp_name)

    output_filename = "output.txt"
    write_to_file(blind_comp_list, output_filename)


get_blind_events()

@app.route('/person/<string:user_id>/pr_history', methods=['GET'])
def pr_history(user_id):

    def better_result(time1, time2):
        if time1 <= 0:
            return time2
        if time2 <= 0:
            return time1
        return min(time1,time2)

    def is_better_result(time1, time2):
        if time1 <= 0 and time2 <= 0:
            return False
        if time1 <= 0:
            return False
        if time2 <= 0:
            return True
        return time1 <= time2

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM Results WHERE personId = %s", [user_id])
    comps = []
    column_names = [column[0] for column in cur.description]
    print(column_names)
    raw_results = cur.fetchall()
    for row in raw_results:
        print(row)
    print("")
    results = [dict(zip(column_names, row)) for row in raw_results]
    for row in results:
        print("gabe: ", end = "")
        print(row)
    print(results)
    print("")
    cur.execute("SELECT DISTINCT competitionId FROM Results WHERE personId = %s", [user_id])

    raw_results = cur.fetchall()
    for row in raw_results:
        comps.append(row[0])

    # dictionary of list of current best result
    comp_results_single = {}
    comp_results_avg = {}
    for event in event_list:
        comp_results_single[event] = -1
        comp_results_avg[event] = -1

    # dictionary of list of avg PRs 
    comp_pr_single = {}
    comp_pr_avg = {} 

    best_pr_streak = 0
    pr_streak = 0
    best_pr_streak_blind = 0
    pr_streak_blind = 0

    cur.execute("CREATE TEMPORARY TABLE UserResults AS SELECT * FROM Results WHERE personId = %s;", [user_id])
    for comp in comps:
        print(comp)

        cur.execute("SELECT * FROM UserResults WHERE competitionId = %s AND personID = %s", (comp, user_id))
        column_names = [column[0] for column in cur.description]
        raw_results = cur.fetchall()
        results = [dict(zip(column_names, row)) for row in raw_results]

        comp_pr_single[comp] = []
        comp_pr_avg[comp] = []
        ## Find the PR in the current comp for each event and update
        for row in results:
            curEvent = row["eventId"]
            if is_better_result(row["best"], comp_results_single[curEvent]):
                comp_pr_single[comp].append((curEvent, row["best"]))
                comp_results_single[curEvent] = better_result(row["best"], comp_results_single[curEvent])

            if is_better_result(row["average"], comp_results_avg[curEvent]):
                comp_pr_avg[comp].append((curEvent, row["average"]))
                comp_results_avg[curEvent] = better_result(row["average"], comp_results_avg[curEvent])    

    for comp in comps:
        print(comp_pr_single[comp])
        print("")
        print(comp_pr_avg[comp])

    # Combine the data
    combined_pr_data = []
    combined_pr_data_blind = []
    for comp in comps:
        comp_data = {
            'comp_name': comp,
            'pr_singles': comp_pr_single.get(comp, []),
            'pr_averages': comp_pr_avg.get(comp, []),
        }
        if comp in blind_comp_list:
            combined_pr_data_blind.append(comp_data)
            if len(comp_pr_single.get(comp, [])) == 0 and len(comp_pr_avg.get(comp, [])) == 0:
                pr_streak_blind = 0
            else:
                pr_streak_blind += 1
            best_pr_streak_blind = max(best_pr_streak_blind,pr_streak_blind)
        else:
            combined_pr_data.append(comp_data)
            combined_pr_data_blind.append(comp_data)
            if len(comp_pr_single.get(comp, [])) == 0 and len(comp_pr_avg.get(comp, [])) == 0:
                pr_streak = 0
                pr_streak_blind = 0
            else:
                pr_streak += 1
                pr_streak_blind += 1
            best_pr_streak_blind = max(best_pr_streak_blind,pr_streak_blind)
            best_pr_streak = max(best_pr_streak,pr_streak)

    print(combined_pr_data)
    return render_template('pr_history.html', pr_streak = pr_streak, best_pr_streak = best_pr_streak,
        pr_streak_blind = pr_streak_blind, best_pr_streak_blind = best_pr_streak_blind, 
        combined_pr_data_blind = combined_pr_data_blind, 
        combined_pr_data=combined_pr_data)

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
        name=person_name, user_id = user_id, pr_history_url=url_for('pr_history', user_id=user_id))

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
