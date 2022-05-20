#!flask/bin/python
from flask import *
from datetime import *
from flask_httpauth import HTTPBasicAuth

auth = HTTPBasicAuth()
app = Flask(__name__)

@app.route('/')
def index():
    abort(418)

users = {}

def make_public_task(task):
    new_task = {}
    for field in task:
        if field == 'id':
            new_task['uri'] = url_for('get_task', task_id=task['id'], _external=True)
        elif field == 'date':
            new_task['date'] = datetime.strftime(task['date'], "%d/%m/%Y")
        else:
            new_task[field] = task[field]
    return new_task

@auth.get_password
def get_password(username):
    if username in users:
        return users[username]['password']
    return None

@app.route('/todo/api/v1.0/auth', methods=['GET'])
@auth.login_required
def authorise():
    return make_response(jsonify({'result': True}), 200)

@app.route('/todo/api/v1.0/register', methods=['POST'])
def register_user():
    if not request.json:
        abort(400)
    if not 'username' in request.json or type(request.json['username']) != str:
        abort(400)
    if request.json['username'] in users:
        abort(409)
    if not 'password' in request.json or type(request.json['password']) != str:
        abort(400)
    users[request.json['username']] = {}
    users[request.json['username']]['password'] = request.json['password']
    users[request.json['username']]['tasks'] = []
    return make_response(jsonify({'result': True}), 201)

@app.route('/todo/api/v1.0/tasks', methods=['GET'])
@auth.login_required
def get_tasks():
    li = users[auth.current_user()]['tasks']
    if request.json:
        if "title_contains" in request.json:
            li = [x for x in li if request.json["title_contains"] in x["title"]]
        if "from_date" in request.json:
            if request.json["from_date"] == "":
                dt = datetime.today().date()
            else:
                try:
                    dt = datetime.strptime(request.json["from_date"],"%d/%m/%Y").date()
                except:
                    return make_response(jsonify({'result': False, 'error': 'Invalid date format.'}), 400)
            li = [x for x in li if dt <= x["date"]]
        if "to_date" in request.json:
            if request.json["to_date"] == "":
                dt = datetime.today().date()
            else:
                try:
                    dt = datetime.strptime(request.json["to_date"],"%d/%m/%Y").date()
                except:
                    return make_response(jsonify({'result': False, 'error': 'Invalid date format.'}), 400)
            li = [x for x in li if dt >= x["date"]]
    if len(li) == 0:
        abort(404)
    return make_response(jsonify({'tasks': [make_public_task(x) for x in li]}), 200)

@app.route('/todo/api/v1.0/tasks/<int:task_id>', methods=['GET'])
@auth.login_required
def get_task(task_id):
    task = [task for task in users[auth.current_user()]['tasks'] if task['id'] == task_id]
    if len(task) == 0:
        abort(404)
    return make_response(jsonify({'task': make_public_task(task[0])}), 200)

@app.route('/todo/api/v1.0/tasks/<int:task_id>', methods=['PUT'])
@auth.login_required
def update_task(task_id):
    task = [task for task in users[auth.current_user()]['tasks'] if task['id'] == task_id]
    if len(task) == 0:
        abort(404)
    if not request.json:
        abort(400)
    if 'title' in request.json and (type(request.json['title']) != str or request.json['title'] == ""):
        return make_response(jsonify({'result': False, 'error': 'Invalid title.'}), 400)
    if 'description' in request.json and type(request.json['description']) is not str:
        return make_response(jsonify({'result': False, 'error': 'Invalid description.'}), 400)
    if 'done' in request.json and type(request.json['done']) is not bool:
        abort(400)
    dt = 0
    if 'date' in request.json:
        try:
            dt = datetime.strptime(request.json['date'], "%d/%m/%Y").date()
        except:
            return make_response(jsonify({'result': False, 'error': 'Invalid date format.'}), 400)
    task[0]['title'] = request.json.get('title', task[0]['title'])
    task[0]['description'] = request.json.get('description', task[0]['description'])
    task[0]['done'] = request.json.get('done', task[0]['done'])
    if dt:
        task[0]['date'] = dt
    return make_response(jsonify({'task': make_public_task(task[0])}), 200)

@app.route('/todo/api/v1.0/tasks/<int:task_id>', methods=['DELETE'])
@auth.login_required
def delete_task(task_id):
    task = [task for task in users[auth.current_user()]['tasks'] if task['id'] == task_id]
    if len(task) == 0:
        abort(404)
    users[auth.current_user()]['tasks'].remove(task[0])
    return make_response(jsonify({'result': True}), 200)

@app.route('/todo/api/v1.0/tasks', methods=['POST'])
@auth.login_required
def create_task():
    if not request.json or not 'title' in request.json or request.json['title'] == "":
        return make_response(jsonify({'result': False, 'error': 'Provide a title.'}), 400)
    if 'description' in request.json and type(request.json['description']) is not str:
        return make_response(jsonify({'result': False, 'error': 'Invalid description.'}), 400)
    if 'date' in request.json:
        try:
            dt = datetime.strptime(request.json['date'], "%d/%m/%Y").date()
        except:
            return make_response(jsonify({'result': False, 'error': 'Invalid date format.'}), 400)
    else:
        dt = datetime.today().date()
    task = {
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False,
        'date': dt
    }
    if len(users[auth.current_user()]['tasks']) == 0:
        task['id'] = 0
    else:
        task['id'] = users[auth.current_user()]['tasks'][-1]['id'] + 1
    users[auth.current_user()]['tasks'].append(task)
    return make_response(jsonify({'result': True, 'task': make_public_task(task)}), 201)

@app.route('/todo/api/v1.0/tasks', methods=['DELETE'])
@auth.login_required
def clean_tasks():
    if not request.json or (not request.json["done"] and not request.json["past"]):
        return make_response(jsonify({'result': False, 'error': 'Specify either done or past tasks to delete.'}), 400)
    copy = [x.copy() for x in users[auth.current_user()]['tasks']]
    for task in copy:
        if request.json["done"] and task["done"]:
            delete_task(task["id"])
        if not (request.json["done"] and task["done"]) and request.json["past"] and task["date"] < datetime.today().date():
            delete_task(task["id"])
    return make_response(jsonify({'result': True, 'deleted': str(len(copy) - len(users[auth.current_user()]['tasks']))}), 200)

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'result': False, 'error': 'Not found'}), 404)

@app.errorhandler(400)
def not_found(error):
    return make_response(jsonify({'result': False, 'error': 'Invalid request'}), 400)

@app.errorhandler(409)
def not_found(error):
    return make_response(jsonify({'result': False, 'error': 'Conflict'}), 409)

@app.errorhandler(405)
def not_found(error):
    return make_response(jsonify({'result': False, 'error': 'Method not allowed'}), 405)

@auth.error_handler
def unauthorized():
    return make_response(jsonify({'result': False, 'error': 'Unauthorized access'}), 403)


if __name__ == '__main__':
    app.run(debug=True)