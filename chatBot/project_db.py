import sqlite3
import time
import json 

class ProjectDb:
    def __init__(self, db_name="project.db"):
        self.conn = sqlite3.connect(db_name)
        self.create_tables()
        self.seed_data()

    def create_tables(self):
        cursor = self.conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Users (
                userId INTEGER PRIMARY KEY,
                email TEXT NOT NULL,
                username TEXT NOT NULL,
                password TEXT NOT NULL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Projects (
                projectId INTEGER PRIMARY KEY,
                userId INTEGER NOT NULL,
                title TEXT,
                text TEXT
            )
        ''')

        self.conn.commit()

    def seed_data(self):
        cursor = self.conn.cursor()

        # Sample users
        users = [
            (1,"admin@tm.com","admin", "md5$c77N8n6nJPb1$3b35343aac5e46740f6e673521aa53dc"),
            (2,"seth@tm.com","seth", "md5$G2RnRaK0svMB$12a67c3542946460e94cd6112d97ec2b"),
            (3,"chris@tm.com","chris", "md5$hb3Anpb9ElaY$0107e413359a8b06d7ac50f5687ffe9d"),
            (4,"ken@tm.com","ken", "md5$Kw9aLHJ4zHLR$2e1e56765119e0158012f77a591be5de"),
            (5,"dade@zerocool.net","dade", "md5$niTI8Z7A9XvV$641ae74c7472d5c907c66994b2289314"),
            (6,"pm@tm.com","pm", "md5$hb3Anpb9ElaY$0107e413359a8b06d7ac50f5687ffe9d")
        ]
        cursor.executemany("INSERT OR IGNORE INTO Users (userId, email, username, password) VALUES (?, ?, ?, ?)", users)

        # Sample projects
        projects = [
            (1, 1, "Default", "AutoThis is the first project"),
            (2, 1, "Default 2", "number 2"),
            (3, 2, "kwjdnf", "wkjfn"),
            (4, 2, "the elephant", "the trunk"),
            (6, 3, "the punks", "little dogs"),
            (7, 4, "Marketing Campaign", "A new marketing campaign needs to be created to promote our new vacuum cleaner product. It will include television, radio, and social media as well as promotions at department stores."),
            (8, 5, "test2", "This is a test project"),
            (9, 6, "ios-app-1", "iOS App Development Project"),
            (10, 6, "android-app-1", "Android App Development Project")
        ]
        cursor.executemany("INSERT OR IGNORE INTO Projects (projectId, userId, title, text) VALUES (?, ?, ?, ?)", projects)

        self.conn.commit()

    def get_user_projects(self, userId):
        cursor = self.conn.cursor()
        cursor.execute(f"SELECT * FROM Projects WHERE userId = '{str(userId)}'")
        rows = cursor.fetchall()

        # Get column names
        columns = [column[0] for column in cursor.description]

        # Convert rows to dictionaries with column names as keys
        projects = [dict(zip(columns, row)) for row in rows]

        # Convert to JSON format
        return json.dumps(projects, indent=4)

    def get_user(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute(
            f"SELECT userId,username FROM Users WHERE userId = {str(user_id)}"
        )
        rows = cursor.fetchall()

        # Get column names
        columns = [column[0] for column in cursor.description]

        # Convert rows to dictionaries with column names as keys
        users = [dict(zip(columns, row)) for row in rows]

        # Convert to JSON format
        return json.dumps(users, indent=4)

    def get_users(self):        
        cursor = self.conn.cursor()
        cursor.execute(
            f"SELECT username,password,userid, email FROM Users"
        )
        rows = cursor.fetchall()

        # Get column names
        columns = [column[0] for column in cursor.description]

        # Convert rows to dictionaries with column names as keys
        users = [dict(zip(columns, row)) for row in rows]

        # Convert to JSON format
        return json.dumps(users, indent=4)
  

    def close(self):
        self.conn.close()
