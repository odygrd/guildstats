
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

class PlayerInfo:
  def __init__(self, rank, name, era, attack, defence, attdef, era_avg_attdef, goods, era_avg_goods):
    self.rank = rank
    self.name = name
    self.era = era
    self.attack = attack
    self.defence = defence
    self.attdef = attdef
    self.era_avg_attdef = era_avg_attdef
    self.goods = goods
    self.era_avg_goods = era_avg_goods


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

    return "{}/player_stats_{}.csv".format(app.config['UPLOAD_FOLDER'], dates[-1]), dates[-1]

def gen_player_stats_grid():
    csv_file, update_date = get_latest_player_stats_file()
    df = pd.read_csv(csv_file)

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
    column_names = ["Score", "Name", "Era", "Attack", "Defense", "Total (Att+Def)", "Era average Att+Def", "Guild Goods", "Era average Guild Goods"]
    df_final = df_final.reindex(columns=column_names)
    df_final.set_index('Score', inplace=True)
    df_final.sort_index(ascending=False,inplace=True)
    df_final.reset_index(drop=True, inplace=True)

    players = []
    rank = 1
    for index, row in df_final.iterrows():
        players.append(PlayerInfo(rank=rank, name=row["Name"], era=row["Era"],
                                  attack=row["Attack"], defence=row["Defense"], attdef=row["Total (Att+Def)"],
                                  era_avg_attdef=int(row["Era average Att+Def"]), goods=row["Guild Goods"],
                                  era_avg_goods=int(row["Era average Guild Goods"])))
        rank = rank + 1
    return players, update_date

@app.route("/")
def index():
    players, update_date = gen_player_stats_grid()
    return render_template('basic_table.html', title='Guild Stats',
                           players=players, update_date=update_date)

@app.route('/', methods=['POST'])
def upload_file():
    uploaded_file = request.files['file']
    if uploaded_file.filename != '':
        uploaded_file.save(os.path.join(app.config['UPLOAD_FOLDER'], uploaded_file.filename))
    return redirect(url_for('index'))