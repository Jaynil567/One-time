from flask import Flask, redirect

app = Flask(__name__)

@app.route("/")
def home():
    return redirect("https://shopkaro-6qlr.onrender.com")

if __name__ == "__main__":
    app.run(debug=True)
