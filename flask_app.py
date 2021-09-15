
# A very simple Flask Hello World app for you to get started with...

import os
import io
import datetime as dt
import pandas as pd
from datetime import datetime
import os
import seaborn as sns
from flask import Flask, Response, render_template, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user
import secrets

APP_FOLDER = '/home/odygrd/guildstats'
UPLOAD_FOLDER = '/home/odygrd/guildstats/uploads'

app = Flask(__name__)

# config
app.config.update(
    DEBUG = True,
    SECRET_KEY = secrets.token_urlsafe(16)
)

login_manager = LoginManager()
login_manager.init_app(app)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# silly user model
class User(UserMixin):
    def __init__(self, id):
        self.id = id
        self.name = "user" + str(id)
        self.password = self.name + "_secret"

    def __repr__(self):
        return "%d/%s/%s" % (self.id, self.name, self.password)


# create some users with ids 1 to 20
users = [User(5)]

class PlayerInfo:
  def __init__(self, rank, name, era, attack, defence, attdef, era_avg_attdef, goods, era_avg_goods, players_count_era):
    self.rank = rank
    self.name = name
    self.era = era
    self.attack = attack
    self.defence = defence
    self.attdef = attdef
    self.era_avg_attdef = era_avg_attdef
    self.goods = goods
    self.era_avg_goods = era_avg_goods
    self.players_count_era = players_count_era


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

    # Count per era
    df_eras_summary = df_final.groupby(['Era']).count()["Name"]

    players = []
    rank = 1
    for index, row in df_final.iterrows():
        players.append(PlayerInfo(rank=rank, name=row["Name"], era=row["Era"],
                                  attack=row["Attack"], defence=row["Defense"], attdef=row["Total (Att+Def)"],
                                  era_avg_attdef=round(row["Era average Att+Def"]), goods=row["Guild Goods"],
                                  era_avg_goods=round(row["Era average Guild Goods"]),
                                  players_count_era=df_eras_summary.loc[row["Era"]]))
        rank = rank + 1

    guild_average_guild_goods = round(df_final["Guild Goods"].mean())
    total_guild_goods = df_final["Guild Goods"].sum()
    return players, update_date, guild_average_guild_goods, total_guild_goods

@app.route("/")
def index():
    players, update_date, guild_average_guild_goods, total_guild_goods = gen_player_stats_grid()
    return render_template('basic_table.html',
                           players=players, update_date=update_date,
                           guild_average_guild_goods=f'{guild_average_guild_goods:,}',
                           total_guild_goods=f'{total_guild_goods:,}')

@app.route("/detail")
@login_required
def detail():
    players, update_date, guild_average_guild_goods, total_guild_goods = gen_player_stats_grid()
    return render_template('detail.html',
                           players=players, update_date=update_date,
                           guild_average_guild_goods=f'{guild_average_guild_goods:,}',
                           total_guild_goods=f'{total_guild_goods:,}')

@app.route("/upload")
@login_required
def upload():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    uploaded_file = request.files['file']
    if uploaded_file.filename != '':
        uploaded_file.save(os.path.join(app.config['UPLOAD_FOLDER'], uploaded_file.filename))
    return redirect(url_for('detail'))

# somewhere to login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if password == username + "_secret":
            id = username.split('user')[1]
            user = User(id)
            login_user(user)
            return redirect(url_for('upload'))
        else:
            return abort(401)
    else:
        return Response('''
        <form action="" method="post">
            <p><input type=text name=username>
            <p><input type=password name=password>
            <p><input type=submit value=Login>
        </form>
        ''')

# handle login failed
@app.errorhandler(401)
def page_not_found(e):
    return Response('<p>Login failed</p>')


# callback to reload the user object
@login_manager.user_loader
def load_user(userid):
    return User(userid)