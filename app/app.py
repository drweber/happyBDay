import re
from jsonschema import validate
from flask import Flask, request, Response, json, abort
from datetime import date, datetime, timedelta
from app import database, models

"""
Regexp_Author:  Radek
Description:    This expression mathes dates formatted as YYYY-MM-DD from 0000-01-01 to 9999-12-31. It checks leap year 
                including all modulo 400, modulo 100 and modulo 4 rules
Matches:        1600-02-29 | 1971-01-31 | 2003-04-30
Non-Matches:    2000-11-31 | 1807-02-29
"""
schema_validation = {
    "type": "object",
    "properties": {
        'dateOfBirth': {
            "type": "string",
            'pattern': '^(((\d{4}-((0[13578]-|1[02]-)(0[1-9]|[12]\d|3[01])|(0[13456789]-|1[012]-)(0[1-9]|['
                       '12]\d|30)|02-(0[1-9]|1\d|2[0-8])))|((([02468][048]|[13579][26])00|\d{2}([13579][26]|0[48]|['
                       '2468][048])))-02-29)){0,10}$'
        }
    }
}

app = Flask(__name__)
database.init_db()

@app.errorhandler(404)
def method_not_allowed(e):
    return json.dumps(
        {
            'error': 'requested location is not allowed',
            'allowed_locations': '/hello/<username>'
        }
    ), 404

@app.errorhandler(405)
def method_not_allowed(e):
    return json.dumps(
        {
            'error': 'requested method is not allowed',
            'allowed_method': 'GET, PUT'
        }
    ), 405

@app.teardown_appcontext
def shutdown_session(execption=None):
    database.db_session.remove()

@app.route('/hello/<string:username>', methods=['GET', 'PUT'])
def hello_world(username):

    if request.method == 'GET':
        now = datetime.now().date()
        ndays = now - timedelta(days=1)
        con = database.engine.connect()
        r = con.execute(models.users.select(models.users.c.username == username)).first()
        con.close()
        if r is not None:
            birhday_date = r[1]
            delta1 = date(now.year, birhday_date.month, birhday_date.day)
            delta2 = date(now.year + 1, birhday_date.month, birhday_date.day)

            if (birhday_date.month > now.month) or ((birhday_date.month == now.month) and (birhday_date.day > now.day)):
                days = (delta1 - ndays).days
                data = {
                    "Message": "Hello " + username + "! Your Birthday is in " + str(days) + " day(s)!"
                }
                message = json.dumps(data)
                resp = Response(message, status=200, mimetype='application/json')
                print()
                return resp

            if birhday_date.month < now.month or ((birhday_date.month == now.month) and (birhday_date.day < now.day)):
                days = (delta2 - ndays).days
                data = {
                    "Message": "Hello " + username + "! Your Birthday is in " + str(days) + " day(s)!"
                }
                message = json.dumps(data)
                resp = Response(message, status=200, mimetype='application/json')
                print()
                return resp

            if (birhday_date.month == now.month) and (birhday_date.day == now.day):
                data = {
                    "Message": "Hello " + username + "! Happy birthday!"
                }
                message = json.dumps(data)
                resp = Response(message, status=200, mimetype='application/json')
                print()
                return resp
        else:
            abort(404, description="User not found")


    if request.method == 'PUT':
        if not request.is_json:
            return json.dumps(
                {
                    'error': 'Data is not valid JSON'
                }
            ), 400
        if not bool(re.match('^[a-zA-Z]+$', username)):
            return json.dumps(
                {
                    'error': 'Data is not valid. Please use only letters for username'
                }
            ), 400
        try:
            validate(request.json, schema_validation)
            dateOfBirth = request.json['dateOfBirth']
        except Exception as e:
            return json.dumps(
                {
                    'error': 'Data is not valid. Please put request in valid JSON schema format'
                }
            ), 400
        dateOfBirth = datetime.strptime(dateOfBirth, "%Y-%m-%d").date()
        con = database.engine.connect()
        r = con.execute(models.users.select(models.users.c.username == username)).first()
        if r:
            con.execute(models.users.update(models.users.c.username == username), birth_date=dateOfBirth)
            return '', 204
        else:
            con.execute(models.users.insert(), username=username, birth_date=dateOfBirth)
            return '', 201
        con.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)