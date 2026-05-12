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


## AI Chatbot

The AI Assistant is integrated into the Django app. After running the server,
log in and click **AI Assistant** in the sidebar.

Configure the OpenAI API key by setting the `OPENAI_API_KEY` environment
variable in `taskManager/settings.py` or via your deployment environment.
