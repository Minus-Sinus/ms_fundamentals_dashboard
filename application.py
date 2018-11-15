import os
import re

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for, jsonify
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash
import datetime

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# custom filter
app.jinja_env.filters["usd"] = usd

# Ensure responses aren't cached


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter used for USD strings
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///ms_dashboard.db")


@app.route("/")
@login_required
def index():
    return render_template("/dashboard.html")


@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    """Show fundamental dashboard"""

    stocks = db.execute("SELECT stock_name || ' (' || symbol || ')' as name_symbol FROM stocks ORDER BY stock_name ASC")

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Get selection from submitted form:
        symbol = str(request.form.get("name_symbol"))
        print("Debug - name_symbol: " + symbol)
        # Save newly chosen stock to database
        # new_symbol = SelectionName.split("(",1)
        # new_symbol = new_symbol[1].split(")",1)
        rows = db.execute("SELECT stock_name FROM stocks WHERE symbol=:sym", sym=symbol)
        SelectionName = rows[0]['stock_name'] + '(' + symbol + ')'

        db.execute("UPDATE users SET Last_stock=:new_sym WHERE id=:uid", uid=session["user_id"], new_sym=symbol)

    # User reached route via GET (as by clicking a link or via redirect), not POST
    else:
        # Read from database what was user's last stock selected:

        try:
            last_stock_symbol = db.execute("SELECT last_stock FROM users WHERE id=:uid", uid=session["user_id"])
            symbol = last_stock_symbol[0]['last_stock']
            if symbol is None:
                symbol = "AAPL"
        except:
            # if lookup of last stock throws an error, go for Apple:
            symbol = "AAPL"

        print("Debug: symbol: " + symbol)
        last_stock_name = db.execute("SELECT stock_name FROM stocks WHERE symbol=:sym", sym=symbol)

        SelectionName = last_stock_name[0]['stock_name'] + ' (' + symbol + ')'

    # populate data list for fundamentals:
    # define data list. Entries are 0..2 for Column 1, 3..5 for column 2, 6..8 for column 3
    charts_info = []

    # Architecture of charts_info:
    # charts_info:
    #   chart_info:
    #     chart_title
    #     left_title
    #     right_title
    #     chart_data

    chart_data = []

    left_axis_titles = ['' for i in range(10)]
    right_axis_titles = ['' for i in range(10)]
    chart_titles = ['' for i in range(10)]
    chart_titles = ['' for i in range(10)]
    y_axis_min_left = ['automatic' for i in range(10)]
    y_axis_min_right = ['automatic' for i in range(10)]
    y_axis_factor_left = [1 for i in range(10)]
    y_axis_factor_right = [1 for i in range(10)]

    # *** Define Left axis titles:
    # ******** Column 1
    i = 0
    chart_titles[i] = "Revenue"
    left_axis_titles[i] = 'Revenue [bn USD]'
    right_axis_titles[i] = 'Growth [%]'
    y_axis_min_left[0] = i
    y_axis_factor_left[i] = 1000  # to get to millions

    i = 1
    chart_titles[i] = "Gross profitability"
    left_axis_titles[i] = 'Gross margin [bn USD]'
    right_axis_titles[i] = 'Gross margin [%]'
    y_axis_min_left[i] = 0
    y_axis_min_right[i] = 0
    y_axis_factor_left[i] = 1000  # to get to millions

    i = 2
    chart_titles[i] = "EBITDA"
    left_axis_titles[i] = 'EBITDA [bn USD]'
    right_axis_titles[i] = 'EBITDA %'
    y_axis_factor_left[i] = 1000  # to get to millions

    # ******** Column 2
    i = 3
    chart_titles[i] = "EBIT"
    left_axis_titles[i] = 'EBIT [bn USD]'
    right_axis_titles[i] = 'EBIT [%]'
    y_axis_factor_left[i] = 1000  # to get to millions

    i = 4
    chart_titles[i] = "Net profit"
    left_axis_titles[i] = 'Net profit [bn USD]'
    right_axis_titles[i] = 'Net profit [%]'
    y_axis_factor_left[i] = 1000  # to get to millions

    i = 5
    chart_titles[i] = "Free Cash-flow"
    left_axis_titles[i] = 'Free Cash-flow [bn USD]'
    right_axis_titles[i] = 'Free Cash-flow [%]'
    y_axis_factor_left[i] = 1000  # to get to millions

    # ******** Column 3
    i = 6
    chart_titles[i] = "Tangible book value (TBV)"
    left_axis_titles[i] = 'Tangible book value [bn USD]'
    right_axis_titles[i] = 'Tangible book value [% of Assets]'
    y_axis_factor_left[i] = 1000  # to get to millions

    i = 7
    chart_titles[i] = "Debt & Leverage"
    left_axis_titles[i] = 'Financial debt [bn USD]'
    right_axis_titles[i] = 'Financial debt [% of TBV]'
    y_axis_factor_left[i] = 1000  # to get to millions

    i = 8
    chart_titles[i] = "Solvency"
    left_axis_titles[i] = 'Quick ratio'
    right_axis_titles[i] = 'Current ratio'

    charts_info = []

    # load fundamental data for chosen stock into fundamentals table from fundamentals_all
    # fundamentals used as a temp table to speed up performance

    # delete old entries from temp table:
    db.execute("DELETE FROM fundamentals")

    # insert relevant data to temp table:
    db.execute("INSERT INTO fundamentals \
                SELECT * FROM fundamentals_all \
                WHERE symbol=:sym", sym=symbol)

    for c in range(1, 4):
        for r in range(1, 4):

            ctr = (c-1) * 3 + r - 1  # counter of chart

            chartname = 'C' + str(c) + 'R' + str(r)

            chart_info = {}

            chart_info['chart_data'] = db.execute("SELECT * FROM (SELECT [xLabel], [Left], [Right] FROM :chartname \
                                                   WHERE symbol=:symbol \
                                                   ORDER BY xLabel DESC LIMIT 32) \
                                                   ORDER BY xLabel ASC", symbol=symbol, chartname=chartname)

            chart_info['chart_title'] = chart_titles[ctr]
            chart_info['left_title'] = left_axis_titles[ctr]
            chart_info['right_title'] = right_axis_titles[ctr]
            chart_info['y_min_left'] = y_axis_min_left[ctr]
            chart_info['y_min_right'] = y_axis_min_right[ctr]
            chart_info['y_axis_factor_left'] = y_axis_factor_left[ctr]
            chart_info['y_axis_factor_right'] = y_axis_factor_right[ctr]

            charts_info.append(chart_info)

    # clean fundamentals temp table
    db.execute("DELETE FROM fundamentals")

    # render html:
    return render_template("dashboard.html", stocks=stocks, charts_info=charts_info, SelectionName=SelectionName, main_heading=SelectionName, sub_heading="Fundamentals Dashboard")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # redirect to home page
        return redirect(url_for("dashboard"))
    # User reached route via GET (as by clicking a link or via redirect), not POST
    else:
        return render_template("login.html", main_heading="Fundamentals dashboard", sub_heading="Login")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")

        # Check if both passwords are the same:
        elif not request.form.get("password") == request.form.get("confirmation"):
            return apology("passwords don't match")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Check if user already exists
        if len(rows) > 0:
            return apology("username already exists")

        # Write new user to database:
        hash = generate_password_hash(request.form.get("password"))
        rows = db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)",
                          username=request.form.get("username"), hash=hash)

        # Identify new user id:
        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Auto log-in new user:
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return render_template("/login.html")

    # User reached route via GET (as by clicking a link or via redirect), not POST
    else:
        return render_template("register.html", main_heading="Fundamentals dashboard", sub_heading="Register new user")


@app.route("/search")
def search():
    """Search for places that match query"""

    # add % to search string to get similar matches
    try:

        str_search = request.args.get("q") + "%"
        str_search = str_search.replace("\'", " ")
        str_search = str_search.replace("\"", " ")
        # print("str_search after replacments: " + str_search)

    except:
        raise ValueError('Missing parameter q in search')
        return jsonify([])

    # search in postal codes of database:
    rows = db.execute("SELECT * FROM stocks \
                      WHERE stock_name LIKE :q \
                      OR symbol LIKE :q", q=str_search)

    return jsonify(rows[:10])


def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
