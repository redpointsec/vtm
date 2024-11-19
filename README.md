```
         __           
___  ___/  |_  _____  
\  \/ /\   __\/     \ 
 \   /  |  | |  Y Y  \
  \_/   |__| |__|_|  /
                   \/                            
```
vtm - an intentionally vulnerable task manager
===

Running vtm
----
### If using mysql:
0. ```mysqladmin -u root create vtmdb```

### continue
1. ```python3 -m venv vtm_venv```
2. ```source vtm_venv/bin/activate```
3. ```pip install -r requirements.txt```
4. ```./manage.py migrate```
5. ```./manage.py loaddata taskManager/fixtures/*```
6. ```./manage.py runserver```
7. Navigate to http://localhost:8000
9. Login with the username `chris` and a password of `test123`


## New Install 

 1. `brew install mysql mysql-client mariadb-connector-c pkgconf`
 2. `brew services start mysql`
 3. `mysqladmin -u root create vtmdb`
 4. `python3.12 -m venv vtm_venv`
 5. `source vtm_venv/bin/activate`
 6. `pip install -r requirements.txt`
 7. `./manage.py migrate`
 8. `./manage.py loaddata taskManager/fixtures/*`
 9. `brew install redis`
 10. `brew services start redis`
 11. `pipenv install python-dotenv`
 12. `cd chatBot`
 13. `cp env.list .env`
 14. Paste Open AI API key into .env file
 15. `cd chatBot`
 16. `streamlit run main.py &; cd ..; ./manage.py runserver` 
 Navigate to http://localhost:8000
 Login with the username `chris` and a password of `test123`
 Navigate to `http://localhost:8502` for the AI Chatbot
