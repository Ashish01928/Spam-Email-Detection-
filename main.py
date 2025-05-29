import streamlit as st
import numpy as np
import pandas as pd
from streamlit_option_menu import option_menu
import time
import joblib
import mysql.connector

def connect_db():
    return mysql.connector.connect(
        host="localhost",      
        user="root",           
        password="yashish2003",
        database="spam_detection"
)


def signup_user(username , mail, password):
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (name , mail, password) VALUES (%s , %s, %s)", (username , mail, password))
        conn.commit()
        return True
    except mysql.connector.Error:
        return False
    finally:
        conn.close()

def login_user(mail, password):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM users WHERE mail = %s", (mail,))
    result = cursor.fetchone()
    conn.close()
    if result and result[0] == password:
        return True
    return False


if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "mail" not in st.session_state:
    st.session_state.mail = ""


custom_css = """
<style>
audio {
    display: none;
}
</style>
"""


st.set_page_config(page_title="Spam Email Detection",page_icon="✉️")


if not st.session_state.logged_in:
    with st.sidebar:
        menu = option_menu(
            menu_title="",
            options=["Login", "Sign Up"],
            icons=["box-arrow-in-right", "person-plus"],
            menu_icon="person-circle",
            default_index=0,
            styles={
                "container": {
                    "padding": "5!important",
                    "background-color": "#262730",  # matching sidebar gray
                },
                "icon": {
                    "color": "white",
                    "font-size": "18px"
                },
                "nav-link": {
                    "font-size": "16px",
                    "text-align": "left",
                    "margin": "5px",
                    "color": "white",
                    "background-color": "#262730",  # keep bg same as sidebar
                    "--hover-color": "#444",  # slightly lighter gray on hover
                },
                "nav-link-selected": {
                    "background-color": "#0c4f97",  # blue selected tab
                    "color": "white",
                }
            }
        )
        
    st.title("Spam Email Detection")

    if menu == "Login":
        st.subheader("Login")

        mail = st.text_input("mail")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if login_user(mail, password):
                st.session_state.logged_in = True
                st.session_state.mail = mail
                st.rerun()
            else:
                st.error("Invalid username or password")

    elif menu == "Sign Up":
        st.subheader("Create a New Account")

        new_username = st.text_input("Name")
        new_mail = st.text_input("mail")
        new_password = st.text_input("Password", type="password")

        if st.button("Sign Up"):
            if signup_user(new_username, new_mail , new_password):
                st.success("Account created successfully! Please login")
            else:
                st.error("Username already exists. Try a different one.")
else:
    mail = st.session_state['mail']
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM users WHERE mail = %s", (mail,))
    name = cursor.fetchone()
    name = name[0]
    cursor.execute("SELECT id FROM users WHERE mail = %s", (mail,))
    userid = cursor.fetchone()
    userid = userid[0]

    conn.close()


    side = option_menu(
        menu_title=None,
        options=['Predict','Contribute','About','Logout',"History"],
        icons=['graph-up-arrow','plus-circle','info-circle','box-arrow-right',"clock-history"],
        menu_icon="cast",
        default_index=0,
        orientation="horizontal"
    )

    if side == 'Predict':
        st.title(f'Welcome Back {name}')

        predict_textt = st.text_area("Enter Your Subject Line :",placeholder="Hey John ! You have won a prize.")
        a,b,c,d = st.columns(4)
        predict_button = a.button("Check",use_container_width=True)

        if predict_button == True:
            if predict_textt != "":
                predict_text = [predict_textt]
                model = joblib.load('model_saved.joblib')
                message_encoder = joblib.load('message_encoder.joblib')

                bar = st.progress(2)
                bar.progress(2,"Loading 2%")
                encoded_text = message_encoder.transform(predict_text)
                encoded_text = encoded_text.toarray()
                ans = model.predict(encoded_text)

                for i in range(3,101):
                    time.sleep(0.03)
                    bar.progress(i,f"Analyzing {i} %")
                
                bar.empty()

                conn = connect_db()
                cursor = conn.cursor()

                if ans[0] == 0:
                    st.success("It is Not a Spam Mail")
                    st.markdown(custom_css,unsafe_allow_html=True)
                    audiofile = "Audio/success.mp3"
                    st.audio(audiofile,autoplay=True)
                    cursor.execute('INSERT INTO history (id, content, prediction) VALUES (%s,%s,"Not Spam")',(userid,predict_textt,))
                else:
                    st.error("It seems to be a Spam Mail")
                    st.markdown(custom_css,unsafe_allow_html=True)
                    audiofile = "Audio/warning.mp3"
                    st.audio(audiofile,autoplay=True)
                    cursor.execute('INSERT INTO history (id, content, prediction) VALUES (%s,%s,"Spam")',(userid,predict_textt,))
                conn.commit()
                conn.close()
            else:
                st.warning("Please Enter a valid Mail !!")

    elif side == 'Contribute':
        st.title("Contribute to dataset 📅")
        mail,target = st.columns([0.7,0.3])

        mail_text = mail.text_area("Enter Mail Content")
        category_selected = target.selectbox(
        "Choose Category",
        ("Spam", "Not Spam"),
        index=0, )
        if category_selected == 'Spam':
            category_selected = 'spam'
        elif category_selected == 'Not Spam':
            category_selected = 'ham'

        a,b,c,d = st.columns([0.4,0.2,0.2,0.2])
        submit_button = a.button("Add To Dataset",use_container_width=True)

        if submit_button == True:

            conn = connect_db()
            cursor = conn.cursor()
        
            cursor.execute("INSERT INTO dataset (category , message) VALUES (%s , %s)", (category_selected,mail_text))
            conn.commit()

            st.success('**Thanks for improving our model!**')
            conn.close()

    elif side =='About':
        st.title("About the project")

        with st.expander("Why Email Spam Detection ?"):
            st.markdown("Without effective spam email detection, individuals and organizations face significant challenges, including increased exposure to phishing attacks, malware, and fraudulent schemes. This leads to security risks, data breaches, reduced productivity due to time spent managing unwanted emails, and increased storage costs. Efficient spam detection is essential for maintaining a secure and efficient communication environment.")

        with st.expander("Objective of this project"):
            st.markdown("The objective of the email spam detection project is to develop an accurate and efficient machine learning model that identifies and filters spam emails, thereby enhancing email security, protecting users from phishing and malware, improving productivity by reducing unwanted emails, and optimizing storage and resource usage.")
        
        with st.expander("Methodology"):
            st.markdown("The methodology involves using Pandas for data cleaning and filtering, preparing the dataset for analysis.")
            st.markdown("A stacking classifier combines Naive Bayes, SVM, and Random Forest algorithms to leverage their strengths in spam detection.")
            st.markdown("Logistic Regression acts as a meta-model to evaluate predictions from the base models.")
            st.markdown("Streamlit facilitates user interaction with a web-based interface, requiring no complex configurations, ensuring easy accessibility via a web browser.")

        with st.expander("How Accurate the models are ?"):
            st.markdown('''The stacking classifier, combining SVM, Random Forest, and Naive Bayes, achieved an accuracy of 98.8% on the testing data, which comprised 20% of the total dataset (amounting to more than 5000 rows).''')
            st.markdown("This accuracy indicates the model's robust performance in accurately detecting spam emails across a substantial dataset")
        
        dev = """
            Developed By:
            ```
            Ashutosh Dash (2101298074)
            Ashish Kumar Sahoo (2101298367)
            ```
            """
        st.info(dev)

    elif side == "History":
        st.title("History ⌚")
        conn = connect_db()
        cursor = conn.cursor()
        query = """
                    SELECT history.created_date, history.content, history.prediction 
                    FROM history 
                    JOIN users ON history.id = users.id 
                    WHERE users.id = %s
                    order by created_date desc
                """
        cursor.execute(query, (userid,))
        rows = cursor.fetchall()

        conn.close()

        df = pd.DataFrame(rows, columns=["Created Date", "Content","Prediction"])

        st.table(df)


    
    elif side == "Logout":
        st.session_state.logged_in = False
        st.session_state.mail = ""
        st.rerun()