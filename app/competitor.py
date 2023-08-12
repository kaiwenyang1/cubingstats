from app import mysql

def get_user_name_mapping():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, name FROM Persons")
    raw_results = cur.fetchall()

    # Convert the raw results to a dictionary
    user_name_mapping = {row[0]: row[1] for row in raw_results}
    return user_name_mapping


