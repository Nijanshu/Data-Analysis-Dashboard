import os
import uuid
import pandas as pd
import matplotlib
# Use 'Agg' backend to avoid GUI/thread issues in web apps
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
from flask import Flask, render_template, request, session, redirect, url_for

app = Flask(__name__)
app.secret_key = "super_secret_key"  # Needed for sessions

UPLOAD_FOLDER = "uploads"
PLOT_FOLDER = "static/plots"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PLOT_FOLDER, exist_ok=True)

def get_df_stats(df):
    return {
        "shape": df.shape,
        "missing": df.isnull().sum().to_dict(),
        "total_missing": int(df.isnull().sum().sum()),
        # We wrap this in a list [ ... ] so that {{ tables[0] }} works
        "tables": [df.describe().to_html(classes="table table-striped table-hover")],
        "columns": df.select_dtypes(include="number").columns.tolist()
    }

@app.route("/dashboard")
def dashboard():
    filepath = session.get("current_file")
    if not filepath:
        return redirect(url_for("index"))

    df = pd.read_csv(filepath)
    df.columns = df.columns.str.strip().str.lower()
    
    context = get_df_stats(df)
    # This passes the dictionary as keyword arguments
    return render_template("dashboard.html", **context)

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("file")
    if not file or file.filename == "":
        return "No file selected", 400

    # Secure the filename and save to session instead of global
    filename = f"{uuid.uuid4()}_{file.filename}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    
    session["current_file"] = filepath
    return redirect(url_for("dashboard"))

@app.route("/plot", methods=["POST"])
def plot():
    filepath = session.get("current_file")
    column = request.form.get("column")

    if not filepath or not column:
        return redirect(url_for("index"))

    df = pd.read_csv(filepath)
    df.columns = df.columns.str.strip().str.lower()

    # Unique filename for the plot to avoid browser caching issues
    plot_filename = f"plot_{uuid.uuid4().hex}.png"
    plot_path = os.path.join(PLOT_FOLDER, plot_filename)

    # Plotting Logic
    plt.figure(figsize=(10, 6))
    df[column].dropna().hist(bins=20, color='#3498db', edgecolor='black')
    plt.title(f"Distribution of {column}")
    plt.grid(axis='y', alpha=0.75)
    plt.savefig(plot_path)
    plt.close() # Important: release memory

    context = get_df_stats(df)
    return render_template("dashboard.html", **context, plot_url=plot_filename)

if __name__ == "__main__":
    app.run(debug=True)