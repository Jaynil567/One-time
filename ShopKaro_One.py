from flask import Flask, redirect,render_template

app = Flask(__name__)

payment=False
@app.route("/")
def home():
    if not payment:
        return render_template("a.html")
    return redirect("https://shopkaro-6qlr.onrender.com")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)


