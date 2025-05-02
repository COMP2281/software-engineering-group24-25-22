# Group 22 - 2024/2025  
**Waterstons Software Engineering Project: Receipt Photo Handling**

---

## Project Overview  
This project focuses on developing an efficient solution for handling and processing receipt photos, helping streamline receipt management processes. The solution is part of a software engineering collaboration with Waterstons.

---

## Team Members

- **Satapas Tanachotpaisit**
- **Kamil Grec**
- **Wilson Arceño**
- **Ben Young**
- **Mosah Hassan**

---

## Project Timeline

For deadlines, assignments, and other project requirements, please refer to the official assignment link below:

[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/vdJ2j5Ot)

# How to run the server deployment in your computer
### Prerequisites
- pip install the `uwsgi` package inside your python development environment. I mean it's already in requirements.txt 
so you can just `pip install -r requirements.txt.` Pip will handle the duplicates don't worry about it. Just run it blindly.
- Install `nginx` in your system. You can do it! Make sure to add it to your system's `%PATH%` or (`$PATH` for unix-like systems). So that your computer will know what it means when you do the command `nginx`. You don't need to do for `uwsgi` since it is already included once your inside your Python virtual environment.


### Running the General Server
#### First run `uwsgi` to make a WSGI container blah blah for the Django codebase. You must be inside the environment when doing this. 
> `uwsgi --socket 127.0.0.1:29000 --chdir <path-to-project>/backend/general --wsgi-file general/wsgi.py --master --processes 10 --threads 2 --stats 127.0.0.1:9191`
#### Then run `nginx` to make a server process. Must be in a new terminal. WSGI is currently running on your first terminal, and you must not close that!
> `nginx -c <path-to-project>/backend/general/server/general-nginx.conf -p <path-to-project>/backend/general/server`
#### To reload the configuration file (if you changed anything)
> `nginx -c <path-to-project>/backend/general/server/general-nginx.conf -p <path-to-project>/backend/general/server -s reload`
#### To close/kill your server
> `nginx -c <path-to-project>/backend/general/server/general-nginx.conf -p <path-to-project>/backend/general/server -s quit`
### Running the Parser Server
> `uwsgi --socket 127.0.0.1:29005 --chdir <path-to-project>/backend/parser --wsgi-file parser/wsgi.py --master --processes 10 --threads 2 --stats 127.0.0.1:9192`
#### Then run `nginx` to make a server process
> `nginx -c <path-to-project>/backend/parser/server/file-parser-nginx.conf -p <path-to-project>/backend/parser/server`
#### To reload the configuration file (if you changed anything)
> `nginx -c <path-to-project>/backend/parser/server/file-parser-nginx.conf -p <path-to-project>/backend/parser/server -s reload`
#### To close/kill your server
> `nginx -c <path-to-project>/backend/parser/server/file-parser-nginx.conf -p <path-to-project>/backend/parser/server -s quit`

### Accessing the servers
- For the General server, type `https://localhost/` in your browser or curl if that is your preference.
- For the File Parser server, type `https://localhost:8080/` in the browser.
