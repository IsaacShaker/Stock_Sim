import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, jsonify
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    username = db.execute('SELECT username FROM users WHERE id=?', session['user_id'])[0]['username']
    stocks = db.execute('SELECT * FROM stock_distribution WHERE user_id=? AND shares>0', session['user_id'])
    cash = (db.execute('SELECT cash FROM users WHERE id=?', session['user_id']))[0]['cash']
    portfolio_value = 0

    # calculate the portfolios current real time total value and alter data so it can be displayed in html
    for stock in stocks:
        data = lookup(stock['symbol'])
        total = data['price'] * stock['shares']
        portfolio_value += total

        stock['name'] = data['name']
        stock['total'] = total
        stock['pl'] = data['price'] - stock['avg_share_price']
        stock['curr_price'] = data['price']

    return render_template("index.html", username=username, stocks=stocks, cash=cash, total=(portfolio_value+cash))


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        symbol = request.form.get("table-symbol") # "table-symbol"
        shares = request.form.get("table-shares") # table-shares
        data = lookup(symbol)

        # the screening has already been done by the search route
        # if these go off, then someone was trying to bypass
        if (not symbol) or (data == None) or (not shares):
            return apology("stop trying to hack!")

        try:
            shares = int(shares)
        except ValueError:
            return apology("stop trying to hack!")

        if (shares < 1):
            return apology("stop trying to hack!")

        user_id = session['user_id']
        cash = (db.execute('SELECT cash FROM users WHERE id=?', user_id))[0]['cash']
        cost = shares*data['price']

        if (cost > cash):
            return apology("Insufficient Funds!")

        # update the transactions table and also the users cash
        db.execute('INSERT INTO transactions (user_id, action, symbol, shares, price_per_share, time) VALUES (?, "buy", ?, ?, ?, ?)', user_id, data["symbol"], shares, data["price"], datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
        db.execute('UPDATE users SET cash=? WHERE id=?', (cash - cost), user_id)

        user_stock = db.execute("SELECT * FROM stock_distribution WHERE user_id=? AND symbol=?", user_id, data['symbol'])

        # if the user has never owned that stock before, create a new row. otherwise, update the existing row
        if len(user_stock) == 0:
            db.execute('INSERT INTO stock_distribution (user_id, symbol, shares, avg_share_price) VALUES (?, ?, ?, ?)', user_id, data['symbol'], shares, data['price'])
        else:
            total_shares = (user_stock[0]['shares'] + shares)
            # calulate new average purchase price
            avg_price = ((user_stock[0]['avg_share_price'] * user_stock[0]['shares']) + (data['price'] * shares)) / float(total_shares)
            db.execute('UPDATE stock_distribution SET avg_share_price=?, shares=? WHERE user_id=? AND symbol=?', avg_price, total_shares, user_id, data['symbol'])

        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("buy.html")


@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    """Get stock quote."""

    if request.method == "POST":
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")
        data = lookup(symbol)

        html = request.args.get("html")
        if html not in ['buy.html', 'sell.html']:
            return apology("naughty boy")

        if not symbol:
            error = "ticker symbol is required"
            return render_template(html, response=error)

        if data == None:
            error = "stock does not exist"
            return render_template(html, response=error)

        if not shares:
            error = "shares is required"
            return render_template(html, response=error)

        try:
            shares = int(shares)
        except ValueError:
            error = "enter a number for shares"
            return render_template(html, response=error)

        if (shares < 1):
            error = "enter a positive number for shares"
            return render_template(html, response=error)

        return render_template(html, symbol=data["symbol"], name=data["name"], price=usd(data["price"]), shares=shares, total=usd(data["price"]*shares), response="")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        # symbol = request.args.get("symbol")
        # data = lookup(symbol)
        # if data == None:
        #     return False

        # return data
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    transactions = db.execute('SELECT action, symbol, shares, price_per_share, time FROM transactions WHERE user_id=? ORDER BY id DESC LIMIT 50', session['user_id'])
    return render_template("history.html", transactions=transactions)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        symbol = request.form.get("symbol")
        data = lookup(symbol)

        if data == None:
            error = "stock does not exist"
            return render_template("quote.html", error=error)

        return render_template("quote.html", symbol=data["symbol"], name=data["name"], price=usd(data["price"]), error="")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("quote.html", symbol="", name="", price="", error="")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Ensure confirmation was submitted
        elif not request.form.get("confirmation"):
            return apology("must confirm password", 400)

        # Ensure passwords match
        if (request.form.get("password") != request.form.get("confirmation")):
            return apology("passwords must match", 400)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username does NOT exist
        if len(rows) != 0 :
            return apology("username already taken", 400)

        # Add user to the database
        db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", request.form.get("username"), generate_password_hash(request.form.get("password")))

        # Redirect user to home page (in this case, they will be prompted to login after registering)
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    if request.method == "POST":
        symbol = request.form.get("table-symbol") # "table-symbol"
        shares = request.form.get("table-shares") # table-shares
        data = lookup(symbol)

        if (not symbol) or (data == None) or (not shares):
            return apology("stop trying to hack!")

        try:
            shares = int(shares)
        except ValueError:
            return apology("stop trying to hack!")

        if (shares < 1):
            return apology("stop trying to hack!")


        user_id = session['user_id']
        cash = (db.execute('SELECT cash FROM users WHERE id=?', user_id))[0]['cash']
        revenue = shares*data['price']

        user_stock = db.execute('SELECT * FROM stock_distribution WHERE user_id=? AND symbol=?', user_id, data["symbol"])

        if (len(user_stock) == 0):
            return apology(f"You don't own any {data['symbol']}")
        elif (user_stock[0]['shares'] < shares):
            return apology(f"You only have {user_stock[0]['shares']} shares")

        # update transactions table and users cash
        db.execute('INSERT INTO transactions (user_id, action, symbol, shares, price_per_share, time) VALUES (?, "sell", ?, ?, ?, ?)', user_id, data["symbol"], shares, data["price"], datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
        db.execute('UPDATE users SET cash=? WHERE id=?', (cash + revenue), user_id)

        # update stock distribution table
        total_shares = (user_stock[0]['shares'] - shares)
        if total_shares == 0:
            db.execute('UPDATE stock_distribution SET avg_share_price=?, shares=? WHERE user_id=? AND symbol=?', 0, total_shares, user_id, data['symbol'])
        else:
            db.execute('UPDATE stock_distribution SET shares=? WHERE user_id=? AND symbol=?', total_shares, user_id, data['symbol'])

        return redirect("/")

    else:
        # stocks = db.execute('SELECT symbol FROM stock_distribution WHERE user_id=? AND shares>0', session['user_id'])
        return render_template("sell.html")
