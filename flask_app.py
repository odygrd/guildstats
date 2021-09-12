
# A very simple Flask Hello World app for you to get started with...

import os
import io
import datetime as dt
import pandas as pd
from datetime import datetime
import os
import seaborn as sns
from flask import Flask, render_template, request, redirect, url_for

APP_FOLDER = '/home/odygrd/guildstats'
UPLOAD_FOLDER = '/home/odygrd/guildstats/uploads'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Returns the file with the latest date
def get_latest_player_stats_file():
    dates = []
    for file in os.listdir(app.config['UPLOAD_FOLDER']):
        #     e.g. 2021-09-01.csv
        filename = file.strip("'")
        filename = filename.split("_")[-1]

        if (filename.split(".")[1] == "csv"):
            date = filename.split(".")[0]
            dates.append(date)

    # Sort the list in ascending order of dates
    dates.sort(key = lambda date: datetime.strptime(date, '%Y-%m-%d'))

    return "{}/player_stats_{}.csv".format(app.config['UPLOAD_FOLDER'], dates[-1])

def gen_player_stats_html():
    df = pd.read_csv(get_latest_player_stats_file())

    sum_column = df["Attack"] + df["Defense"]
    df["Total (Att+Def)"] = sum_column
    column_names = ["Score", "Name", "Era", "Attack", "Defense", "Total (Att+Def)", "Guild Goods"]
    df = df.reindex(columns=column_names)
    df.set_index('Era',inplace=True)

    # Calculate Averages
    df_mean = df.groupby('Era').mean()
    df_mean = df_mean.drop(columns='Attack')
    df_mean = df_mean.drop(columns='Defense')
    df_mean = df_mean.drop(columns='Score')
    df_mean = df_mean.rename(columns={"Total (Att+Def)": "Era average Att+Def", "Guild Goods": "Era average Guild Goods"})

    # Join into a single df
    df_final = df.join(df_mean)
    df_final.reset_index(drop=False, inplace=True)
    print(tabulate(df_final, headers='keys', tablefmt='fancy_grid'))
    column_names = ["Score", "Name", "Era", "Attack", "Defense", "Total (Att+Def)", "Era average Att+Def", "Guild Goods", "Era average Guild Goods"]
    df_final = df_final.reindex(columns=column_names)
    df_final.set_index('Score', inplace=True)
    df_final.sort_index(ascending=False,inplace=True)
    df_final.reset_index(drop=True, inplace=True)

    styled_df = df_final.style.background_gradient(cmap=sns.light_palette("green", as_cmap=True), subset=pd.IndexSlice[df_final['Guild Goods']>=2357, 'Guild Goods']).background_gradient(cmap=sns.light_palette("red", as_cmap=True, reverse=True), subset=pd.IndexSlice[df_final['Guild Goods']<2357, 'Guild Goods']).background_gradient(cmap=sns.light_palette("purple", as_cmap=True), subset=['Total (Att+Def)']).format(precision = 0).set_table_styles([{"selector": "", "props": [("border", "1px solid grey")]},{"selector": "tbody td", "props": [("border", "1px solid grey")]},{"selector": "th", "props": [("border", "1px solid grey")]}])
    return styled_df.render()

@app.route('/upload')
def upload_form():
   return render_template('upload.html')

@app.route("/")
def index():
    return render_template("index.html")

@app.route('/upload', methods = ['GET', 'POST'])
def upload_file():
    uploaded_file = request.files['file']
    if uploaded_file.filename != '':
        uploaded_file.save(os.path.join(app.config['UPLOAD_FOLDER'], uploaded_file.filename))
        data = gen_player_stats_html()
    return render_template("index.html", data=data)