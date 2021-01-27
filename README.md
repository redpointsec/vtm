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
1. ```mysqladmin -u root create vtmdb```
2. ```python3 -m venv vtm_venv```
3. ```source vtm_venv/bin/activate```
4. ```pip install -r requirements.txt```
5. ```./manage.py migrate```
6. ```./manage.py loaddata taskManager/fixtures/*```
7. ```./manage.py runserver```
8. Navigate to http://localhost:8000
9. Login with the username `chris` and a password of `test123`

