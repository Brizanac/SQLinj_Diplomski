import sqlite3, os, hashlib
from flask import Flask, jsonify, render_template, request, g

app = Flask(__name__)
app.database = "sample.db"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/restock')
def restock():
    return render_template('restock.html')

@app.route('/api/v1.0/storeLoginAPI/', methods=['POST'])
def loginAPI():
    if request.method == 'POST':
        uname,pword = (request.json['username'],request.json['password'])
        g.db = connect_db()
        cur = g.db.execute("SELECT * FROM employees WHERE username = '%s' AND password = '%s'" %(uname, hash_pass(pword)))
        if cur.fetchone():
            result = {'status': 'success'}
        else:
            result = {'status': 'fail'}
        g.db.close()
        return jsonify(result)

@app.route('/api/v1.0/storeAPI', methods=['GET', 'POST'])
def storeapi():
    if request.method == 'GET':
        g.db = connect_db()
        curs = g.db.execute("SELECT * FROM shop_items")
        cur2 = g.db.execute("SELECT * FROM employees")
        items = [{'items':[dict(name=row[0], quantity=row[1], price=row[2]) for row in curs.fetchall()]}]
        empls = [{'employees':[dict(username=row[0], password=row[1]) for row in cur2.fetchall()]}]
        g.db.close()
        return jsonify(items+empls)

    elif request.method == 'POST':
        g.db = connect_db()
        name,quan,price = (request.json['name'],request.json['quantity'],request.json['price'])
        curs = g.db.execute("""INSERT INTO shop_items(name, quantitiy, price) VALUES(?,?,?)""", (name, quan, price))
        g.db.commit()
        g.db.close()
        return jsonify({'status':'OK','name':name,'quantity':quan,'price':price})

@app.route('/api/v1.0/storeAPI/<item>', methods=['GET'])
def searchAPI(item):
    g.db = connect_db()
    try:
    #curs = g.db.execute("SELECT * FROM shop_items WHERE name=?", item) #The safe way to actually get data from db
        curs = g.db.execute("SELECT * FROM shop_items WHERE name = '%s'" %item)
        results = [dict(name=row[0], quantity=row[1], price=row[2]) for row in curs.fetchall()]
        g.db.close()
        return jsonify(results)
    except sqlite3.OperationalError as e:
        error_message = f"An error occurred: {e}"
        app.logger.error(error_message)  # Log the error
        return jsonify({"error": error_message}), 500
    
@app.route('/api/v1.0/servicesAPI', methods=['GET'])
def servicesapi():
    if request.method == 'GET':
        g.db = connect_db()
        curs = g.db.execute("SELECT * FROM services")
        services = [{'services': [dict(name=row[0], code=row[1], date=row[2]) for row in curs.fetchall()]}]
        g.db.close()
        return jsonify(services)

@app.route('/api/v1.0/servicesAPI/<service>', methods=['GET'])
def search_serviceAPI(service):
    g.db = connect_db()
    curs = g.db.execute("SELECT * FROM services WHERE name = ?", (service,))
    results = [dict(name=row[0], code=row[1], date=row[2], availability=row[3]) for row in curs.fetchall()]
    g.db.close()
    return jsonify(results)

    
@app.errorhandler(404)
def page_not_found_error(error):
    return render_template('error.html', error=error)

@app.errorhandler(500)
def internal_server_error(error):
    return render_template('error.html', error=error)

def connect_db():
    return sqlite3.connect(app.database)

# Create password hashes
def hash_pass(passw):
	m = hashlib.md5()
	m.update(passw.encode('utf-8'))
	return m.hexdigest()

if __name__ == "__main__":

    if not os.path.exists(app.database):
        with sqlite3.connect(app.database) as connection:
            c = connection.cursor()
            c.execute("""CREATE TABLE shop_items(name TEXT, quantity TEXT, price TEXT)""")
            c.execute("""CREATE TABLE employees(username TEXT, password TEXT)""")
            c.execute("""CREATE TABLE services(name TEXT, code TEXT, date TEXT, availability TEXT)""")
            c.execute('INSERT INTO shop_items VALUES("water", "40", "100")')
            c.execute('INSERT INTO shop_items VALUES("juice", "40", "110")')
            c.execute('INSERT INTO shop_items VALUES("candy", "100", "10")')
            c.execute('INSERT INTO employees VALUES("admin", "{}")'.format(hash_pass("badword")))
            c.execute('INSERT INTO employees VALUES("theeguy9", "{}")'.format(hash_pass("badpassword")))
            c.execute('INSERT INTO employees VALUES("newguy29", "{}")'.format(hash_pass("pass123")))
            c.execute('INSERT INTO services VALUES("cleaning", "CLEAN123", "2023-08-09", "available")')
            connection.commit()  # Commit before exiting the 'with' block

app.run(host='0.0.0.0')
