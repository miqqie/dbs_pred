
from flask import Flask, render_template, request
from groq import Groq
import joblib
import os
import requests
import sqlite3

os.environ['GROQ_API_KEY'] = os.getenv("groq")

app = Flask(__name__)

@app.route("/",methods=["GET","POST"])
def index():
    return(render_template("index.html"))

@app.route("/main",methods=["GET","POST"])
def main():
    username = request.form.get("q")
    if not username:
        username = "there"
    else:
        # Save username to database
        conn = sqlite3.connect('user.db')
        c = conn.cursor()
        # Insert the username - table has columns (name, timestamp)
        import datetime
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO user VALUES (?, ?)", (username, current_time))
        conn.commit()
        conn.close()
    return(render_template("main.html", username=username))

@app.route("/llama",methods=["GET","POST"])
def llama():
    return(render_template("llama.html"))

@app.route("/deepseek",methods=["GET","POST"])
def deepseek():
    return(render_template("deepseek.html"))

@app.route("/deepseek_llama",methods=["GET","POST"])
def deepseek_llama():
    return(render_template("deepseek_llama.html"))

@app.route("/telegram",methods=["GET","POST"])
def telegram():
    domain_url = "https://dbs-pred-kds3.onrender.com"

    # The following line is used to delete the existing webhook URL for the Telegram bot
    delete_webhook_url = f"https://api.telegram.org/bot{os.environ.get('TELEGRAM_BOT_TOKEN')}/deleteWebhook"
    webhook_response = requests.post(delete_webhook_url, json={"url": domain_url, "drop_pending_updates": True})

    # Set the webhook URL for the Telegram bot
    set_webhook_url = f"https://api.telegram.org/bot{os.environ.get('TELEGRAM_BOT_TOKEN')}/setWebhook?url={domain_url}/webhook"
    webhook_response = requests.post(set_webhook_url, json={"url": domain_url, "drop_pending_updates": True})

    if webhook_response.status_code == 200:
        # set status message
        status = "The telegram bot is running. Please check with the telegram bot. @rinnie_dsai_bot"
    else:
        status = "Failed to start the telegram bot. Please check the logs."
    
    return(render_template("telegram.html", status=status))

@app.route("/stop telegram",methods=["GET","POST"])
def stop_telegram():
    domain_url = "https://dbs-pred-kds3.onrender.com"

    # The following line is used to delete the existing webhook URL for the Telegram bot
    delete_webhook_url = f"https://api.telegram.org/bot{os.environ.get('TELEGRAM_BOT_TOKEN')}/deleteWebhook"
    webhook_response = requests.post(delete_webhook_url, json={"url": domain_url, "drop_pending_updates": True})

    if webhook_response.status_code == 200:
        # set status message
        status = "The telegram bot has stopped."
    else:
        status = "Failed to stop the telegram bot. Please check the logs."
    
    return(render_template("telegram.html", status=status))

@app.route("/webhook",methods=["GET","POST"])
def webhook():

    # This endpoint will be called by Telegram when a new message is received
    update = request.get_json()
    if "message" in update and "text" in update["message"]:
        # Extract the chat ID and message text from the update
        chat_id = update["message"]["chat"]["id"]
        query = update["message"]["text"]

        # Pass the query to the Groq model
        client = Groq()
        completion_ds = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "user",
                    "content": query
                }
            ]
        )
        response_message = completion_ds.choices[0].message.content

        # Send the response back to the Telegram chat
        send_message_url = f"https://api.telegram.org/bot{os.environ.get('TELEGRAM_BOT_TOKEN')}/sendMessage"
        requests.post(send_message_url, json={
            "chat_id": chat_id,
            "text": response_message
        })
    return('ok', 200)

@app.route("/dbs",methods=["GET","POST"])
def dbs():
    return(render_template("dbs.html"))

@app.route("/llama_reply",methods=["GET","POST"])
def llama_reply():
    q = request.form.get("q")
    # load model
    client = Groq()
    completion = client.chat.completions.create(
    model="llama-3.1-8b-instant",
    messages=[
        {
            "role": "user",
            "content": q
        }
    ]
)
    # Format text with ** to HTML bold tags
    import re
    response_content = completion.choices[0].message.content
    formatted_content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', response_content)
    
    return(render_template("llama_reply.html",r=formatted_content))

@app.route("/deepseek_reply",methods=["GET","POST"])
def deepseek_reply():
    q = request.form.get("q")
    # load model
    client = Groq()
    completion = client.chat.completions.create(
    model="deepseek-r1-distill-llama-70b",
    messages=[
        {
            "role": "user",
            "content": q
        }
    ]
)
    # Get the response content
    response_content = completion.choices[0].message.content
    
    # Remove content between <think> and </think> tags
    import re
    cleaned_response = re.sub(r'<think>.*?</think>', '', response_content, flags=re.DOTALL)
    
    # Remove extra spaces at the top
    cleaned_response = cleaned_response.lstrip()
    
    # Format text with ** to HTML bold tags
    formatted_response = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', cleaned_response)
    
    return(render_template("deepseek_reply.html",r=formatted_response))

@app.route("/deepseek_llama_reply",methods=["GET","POST"])
def deepseek_llama_reply():
    q = request.form.get("q")

    # Initialize client
    client = Groq()

    # Call DeepSeek model
    deepseek_response = client.chat.completions.create(
        model="deepseek-r1-distill-llama-70b",
        messages=[{"role": "user", "content": q}]
    )

    # Call LLaMA model
    llama_response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": q}]
    )

    # Extract content
    deepseek_answer = deepseek_response.choices[0].message.content
    llama_answer = llama_response.choices[0].message.content
    
    # Remove content between <think> and </think> tags from Deepseek response
    import re
    cleaned_deepseek = re.sub(r'<think>.*?</think>', '', deepseek_answer, flags=re.DOTALL)
    
    # Remove extra spaces at the top
    cleaned_deepseek = cleaned_deepseek.lstrip()
    
    # Format text with ** to HTML bold tags
    formatted_deepseek = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', cleaned_deepseek)
    formatted_llama = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', llama_answer)

    return render_template(
        "deepseek_llama_reply.html",
        deepseek=formatted_deepseek,
        llama=formatted_llama
    )
@app.route("/user_log",methods=["GET","POST"])
def user_log():
    try:
        conn = sqlite3.connect('user.db')
        c = conn.cursor()
        
        # Get all users - the table has columns (name, timestamp)
        c.execute('''SELECT * FROM user''')
        rows = c.fetchall()
        
        # Format the results
        if rows:
            r = "\n".join([f"Name: {row[0]}, Time: {row[1]}" for row in rows])
        else:
            r = "No user logs found. The log is empty."
        
        c.close()
        conn.close()
        return render_template("user_log.html", r=r)
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route("/delete_log",methods=["GET","POST"])
def delete_log():
    try:
        conn = sqlite3.connect('user.db')
        cursor = conn.cursor()
        
        # First get all logs to display what was deleted
        cursor.execute('SELECT * FROM user')
        rows = cursor.fetchall()
        
        if rows:
            r = "\n".join([f"Name: {row[0]}, Time: {row[1]}" for row in rows])
        else:
            r = "No logs to delete. The log was already empty."
        
        # Then delete all logs
        cursor.execute('DELETE FROM user')
        conn.commit()
        conn.close()
        
        return render_template("delete_log.html", r=r)
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/sepia', methods=['GET', 'POST'])
def sepia():
    return render_template("sepia_hf.html")

@app.route("/prediction",methods=["GET","POST"])
def prediction():
    q = float(request.form.get("q"))
    # load model
    model = joblib.load("dbs.jl")
    # make prediction
    pred = model.predict([[q]])
    # Format the prediction: remove brackets and round to 2 decimal places
    formatted_pred = round(float(pred[0]), 2)
    return(render_template("prediction.html",r=formatted_pred))

if __name__ == "__main__":
    app.run()

