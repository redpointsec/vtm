vtm - an intentionally vulnerable task manager
===

Running vtm
----
1. ```mysqladmin -u root create vtmdb```
2. ```pip3 install -r requirements.txt```
3. ```python3 manage.py migrate```
4. ```python3 manage.py loaddata taskManager/fixtures/*```
5. ```python3 manage.py runserver```
6. Navigate to http://localhost:8000
7. Login with the username `chris` and a password of `test123`

