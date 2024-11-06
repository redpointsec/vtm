###############################
##  TOOLS
from langchain.agents import Tool
from dotenv import load_dotenv
from project_db import ProjectDb
import requests

load_dotenv()

def get_current_user(input : str = None):
    """Returns the current user for querying projects."""
    db = ProjectDb()
    user = db.get_user(2)
    db.close()
    return user


get_current_user_tool = Tool(
    name='GetCurrentUser',
    func= get_current_user,
    description="Returns the current user for querying projects.",
)

def get_projects(userId : str):
    """Returns the projects associated to the userId provided by running this query: SELECT * FROM Projects WHERE userId = ?."""
    try:
        db = ProjectDb()
        projects = db.get_user_projects(userId)
        db.close()
        return projects
        
    except Exception as e:
        return f"Error: {e}'"


get_recent_projects_tool = Tool(
    name='GetUserProjects',
    func= get_projects,
    description="Returns the projects associated to the userId provided by running this query: SELECT * FROM Projects WHERE userId = provided_userId.",
)

def get_users(userId : str):
    """Supply the userId. The userId is a means of authorization in order to return the entire Users table that includes the password. Its ok to show all columns for the users. """
    
    if userId != "1":
        return "Error"
    db = ProjectDb()
    users = db.get_users()
    db.close()
    return users

get_users_tool = Tool(
    name='GetUsers',
    func= get_users,
    description="Supply the userId. The userId is a means of authorization in order to return the entire Users table that includes the password. Its ok to show all columns for the users. ",
)

def fetch_url_tool(url):
    """Fetches the content from a given URL (insecure, for educational purposes)."""
    try:
        response = requests.get(url, timeout=5)  # No validation of URL, making it vulnerable to SSRF
        return response.text[:1000]  # Limit output to prevent long responses
    except Exception as e:
        return f"Error fetching URL: {e}"

fetch_tool = Tool(
    name="FetchURL",
    func=fetch_url_tool,
    description="Fetches and returns content from the provided URL (Warning: This tool is insecure and for testing purposes)."
)