import streamlit as st
import base64

def display_instructions():
    # Markdown with some basic CSS styles for the box
    box_css = """
    <style>
        .instructions-box {
            background-color: #f0f0f0;
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 20px;
            color: #3f3f3f;
        }
    </style>
    """

    st.sidebar.markdown(box_css, unsafe_allow_html=True)

    st.sidebar.markdown(
        """
    <div class="instructions-box" >
        
    <h2 style="color:#3f3f3f"> Instructions </h2>
    You can exploit this assistant via prompt 
    injection to get two flags.

    To help you finish the challenge, we suggest you familiarize yourself with the techniques 
    described <a href="https://labs.withsecure.com/publications/llm-agent-prompt-injection" target="_blank">here</a> 
    and <a href="https://youtu.be/43qfHaKh0Xk" target="_blank">here</a>.

    </div>
    <b>Please do not do any brute forcing attacks here, you will only waste your time. </b>
    You'll also find the database schema to be useful:

    """,
        unsafe_allow_html=True,
    )

    if st.sidebar.button('Show database schema', use_container_width=True):
        st.sidebar.info('Users(userId,email,username,password)\n\nProjects(projectId,userid,title,text)')



# Function to convert image to base64
def get_image_base64(path):
    with open(path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
    return encoded_string

def display_logo():
    # Convert your image
    image_base64 = get_image_base64("vtm-logo.png")

    # URL of the company website
    url = 'https://vtm-ctf.rdpt.dev/'

    # HTML for centered image with hyperlink
    html_string = f"""
    <div style="display:flex; justify-content:center;">
        <a href="{url}" target="_blank">
        <img src="data:image/png;base64,{image_base64}" width="150px">
        </a>
    </div>
    """
    # Display the HTML in the sidebar
    st.sidebar.markdown(html_string, unsafe_allow_html=True)
