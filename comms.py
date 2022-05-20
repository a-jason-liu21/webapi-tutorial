import requests

base_url = "http://127.0.0.1:5000/todo/api/v1.0/"
commands = {}
username = ""
password = ""

def get_credentials():
    global username
    global password
    success = False
    proceed_login = False
    while not success:
        
        proceed_login = False
        if input("Register new user (Y/N): ").lower() == 'y':
            username = input("Choose username: ")
            password = input("Choose password: ")
            data = {"username" : username, "password" : password}
            req = requests.post(base_url + "register", json = data)
            if req.status_code == 409:
                print("Username is taken.")
            elif req.status_code == 400:
                print("Username or password is invalid.")
            elif req.status_code == 201:
                print("Registered successfully.")
                proceed_login = True
            else:
                print("An unknown error occurred.")
        else:
            proceed_login = True

        if proceed_login:
            username = input("Enter username: ")
            password = input("Enter password: ")
            req = requests.get(base_url + "auth", auth = (username, password))
            success = req.json()['result']
            if req.status_code == 403:
                print("Incorrect credentials.")
            elif req.status_code == 200:
                print("Logged in as " + username + ".")
            else:
                print("An error occurred.")

def print_help():
    print("Commands:")
    for key, val in commands.items():
        print(key.ljust(10) + "| " + val[1])

def quit():
    exit(0)

def logout():
    global username
    global password
    username = ""
    password = ""
    print("Logged out.")
    get_credentials()

def print_task(task):
    print("Task:".ljust(15) + task["title"] + " | ID: " + task["uri"].split("/")[-1])
    if task["description"] != "":
        print("Description:".ljust(15) + task["description"])
    print("Date:".ljust(15) + task["date"])
    print("Completed:".ljust(15) + ["No", "Yes"][task["done"]])
    print()

def list_tasks():
    req = requests.get(base_url + "tasks", auth = (username, password), json = {})
    if req.status_code == 404:
        print("No tasks found.")
        return
    elif req.status_code == 200:
        print("All tasks: ")
        print()
        for task in req.json()["tasks"]:
            print_task(task)
    else:
        print("An error occurred.")

def query_title():
    filter = input("Title contains: ")
    data = {"title_contains": filter}
    req = requests.get(base_url + "tasks", auth = (username, password), json = data)
    if req.status_code == 404:
        print("No tasks found.")
        return
    elif req.status_code == 200:
        print("Tasks with '" + filter + "' in title: ")
        print()
        for task in req.json()["tasks"]:
            print_task(task)
    else:
        print("An error occurred.")

def query_date():
    from_date = input("From date ('dd/mm/yyyy', defaults to today): ")
    to_date = input("To date ('dd/mm/yyyy', defaults to from date): ")
    to_date = [to_date, from_date][to_date == ""]
    data = {"from_date": from_date, "to_date": to_date}
    req = requests.get(base_url + "tasks", auth = (username, password), json = data)
    if req.status_code == 400:
        print("Error: " + req.json()["error"])
        return
    elif req.status_code == 404:
        print("No tasks found.")
        return
    elif req.status_code == 200:
        print("Tasks in date range: ")
        print()
        for task in req.json()["tasks"]:
            print_task(task)
    else:
        print("An error occurred.")

def new_task():
    title = input("Task title: ")
    desc = input("Enter description: ") 
    date = input("Enter date ('dd/mm/yyyy', defaults to today): ")
    data = {"title": title}
    if desc:
        data["description"] = desc
    if date:
        data["date"] = date
    req = requests.post(base_url + "tasks", auth = (username, password), json = data)
    if req.status_code == 400:
        print("Error: " + req.json()["error"])
    elif req.status_code == 201:
        print("Task created with ID " + req.json()["task"]["uri"].split("/")[-1])
    else:
        print("An error occurred.")

def get_task():
    id = input("Task ID: ")
    req = requests.get(base_url + "tasks/" + id, auth = (username, password))
    if req.status_code == 404 or req.status_code == 405:
        print("ID not found. Use an integer ID from 'tasks' or 'query'/'qdate'.")
    elif req.status_code == 200:
        print_task(req.json()["task"])
    else:
        print("An error occurred.")

def mark_done():
    id = input("Task ID: ")
    data = {"done": True}
    req = requests.put(base_url + "tasks/" + id, auth = (username, password), json = data)
    if req.status_code == 404 or req.status_code == 405:
        print("ID not found. Use an integer ID from 'tasks' or 'query'/'qdate'.")
    elif req.status_code == 200:
        print("Marked task " + id + " as done.")
    else:
        print("An error occurred.")

def edit_task():
    id = input("Task ID: ")
    title = input("New title: ")
    desc = input("New description: ") 
    date = input("New date ('dd/mm/yyyy', defaults to today): ")
    done = input("Completed (Y/N): ")
    data = {}
    if title != "":
        data["title"] = title
    if desc != "":
        data["description"] = desc
    if date != "":
        data["date"] = date
    if done != "":
        data["done"] = (done.lower() == "y")
    req = requests.put(base_url + "tasks/" + id, auth = (username, password), json = data)
    if req.status_code == 404 or req.status_code == 405:
        print("ID not found. Use an integer ID from 'tasks' or 'query'/'qdate'.")
    elif req.status_code == 200:
        print("Marked task " + id + " as done.")
    elif req.status_code == 400:
        print("Error: " + req.json()["error"])
    else:
        print("An error occurred.")

def delete_task():
    id = input("Task ID: ")
    req = requests.delete(base_url + "tasks/" + id, auth = (username, password))
    if req.status_code == 404 or req.status_code == 405:
        print("ID not found. Use an integer ID from 'tasks' or 'qtitle'/'qdate'.")
    elif req.status_code == 200:
        print("Deleted task " + id + ".")
    else:
        print("An error occurred.")

def clean_tasks():
    done = input("Delete finished tasks (Y/N): ")
    past = input("Delete past tasks (Y/N): ")
    data = {"done": (done.lower() == "y"), "past": (past.lower() == "y")}
    req = requests.delete(base_url + "tasks", auth = (username, password), json = data)
    if req.status_code == 400:
        print("Error: " + req.json()["error"])
    elif req.status_code == 200:
        print("Successfully cleaned " + req.json()["deleted"] + " item(s).")
    else:
        print("An error occurred.")


commands = {
    "help": [print_help, "Prints this help information."],
    "exit": [quit, "Quits the app."],
    "logout": [logout, "Logs out the current user."], 
    "tasks": [list_tasks, "Lists all tasks."],
    "qtitle": [query_title, "Queries tasks by title."],
    "qdate": [query_date, "Queries tasks by date."],
    "new": [new_task, "Creates a new task."],
    "view": [get_task, "Views a task ID."],
    "done": [mark_done, "Mark a task ID as done."],
    "edit": [edit_task, "Edits a task ID."],
    "del": [delete_task, "Deletes a task ID."],
    "clean": [clean_tasks, "Deletes completed or past tasks."]
}

print("- Todo API Tutorial App -")
get_credentials()
while True:
    command = input("Enter command: ")
    try:
        commands[command][0]()
    except KeyError:
        print("Unrecognised command. Try 'help' for a list of commands.")
