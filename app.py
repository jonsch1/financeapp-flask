import os


from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# Set up database
os.environ["DATABASE_URL"] = "postgres://rihwzyhaltmydz:2ee8e5f0380167cae24e01ee411f18526a71c928aaa47847c11bd9b31a3d3ba3@ec2-54-247-125-116.eu-west-1.compute.amazonaws.com:5432/d3sqngohgn6ob4"
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
@login_required
def index():

    userid=session["user_id"]
    """Show portfolio of stocks"""
    # which stocks the user owns, the numbers of shares owned, the current price of each stock,
    #and the total value of each holding (i.e., shares times price).
    #Also display the user’s current cash balance along with a grand total (i.e., stocks' total value plus cash).
    users = db.execute("SELECT cash FROM users WHERE id = :id",id=userid)
    balance=round(users[0]['cash'],2)

    portfolio = db.execute("SELECT * FROM portfolio WHERE id = :id",id=userid)

    networth=balance

    #append stocks*shares to values
    for i in portfolio:

        totalvalue=lookup(i['symbol'])["price"]*i['shares']
        networth+=lookup(i['symbol'])["price"]*i['shares']
        symbol=i['symbol']
        db.execute("UPDATE portfolio SET totalvalue = :totalvalue WHERE id = :id AND symbol= :symbol;", id=userid, symbol=symbol, totalvalue=totalvalue)


    #round networth to 2 digits a   fter .
    networth=round(networth,2)
    portfolio = db.execute("SELECT * FROM portfolio WHERE id = :id",id=userid)
    return render_template("index.html", portfolio=portfolio, balance=balance, networth=networth)
    return apology("TODO")


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    print ("test123")

    """Buy shares of stock"""
    if request.method== "POST":
        userid=session["user_id"]
        symbol=request.form.get("symbol")
        operation="buy"
        try:
            shares = int(request.form.get("shares"))
            if shares < 0:
                return apology("Shares must be positive integer")
        except:
            return apology("Shares must be positive integer")

        print(shares,symbol,userid)
        print ("test1234")

        if symbol==None:
            return apology("must provide symbol", 403)
        #check prize and compare to current account balance
        else:
            if(lookup(symbol)==None):
                print ("test12345")
                return apology("couldn't find symbol")
            else:
                print("HALLO")
                print(lookup(symbol)["price"])

                price=lookup(symbol)["price"]*shares
                balance=db.execute("SELECT cash FROM users WHERE id = :id", id=userid)[0]["cash"]
                print(balance)
                if (price>balance):
                    return apology ("You are too poor")
                else:
                    print("test1234567")
                    #let them pay
                    db.execute("UPDATE users SET cash= :balance - :price WHERE id = ':id'", id=userid, price=price, balance=balance)
                   #update their history
                    db.execute("INSERT INTO history (id, operation, symbol, shares) VALUES(':id', :operation, :symbol, ':shares'); ", id=userid, operation=operation, symbol=symbol, shares=shares)
                   #update their portfolio
                    rows=db.execute("SELECT 'shares' FROM 'portfolio' WHERE id = :id AND symbol= :symbol", id=userid, symbol=symbol)
                   #make sure there isnt already shares of same company
                    if len(rows)!=1:
                        #INSERT new row
                        db.execute("INSERT INTO portfolio (id, symbol, shares) VALUES(':id', :symbol, ':shares'); ", id=userid, symbol=symbol, shares=shares)
                    else:
                        #update old row
                        db.execute("UPDATE portfolio SET shares = shares + :shares WHERE id = :id AND symbol= :symbol;", id=userid, symbol=symbol, shares=shares)

            #redirect
            return redirect("/")







    return render_template("buy.html")
    return apology("TODO")


@app.route("/history")
@login_required
def history():

    userid=session["user_id"]
    """Show history of transactions"""
    history = db.execute("SELECT * FROM history WHERE id = :id",id=userid)
    return render_template("history.html", history=history)
    return apology("TODO")


@app.route("/login", methods=["GET", "POST"])
def login():
    print ("test")
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
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

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
    #get symbol from html form

    #execute lookup(symbol)
    if request.method == "POST":
        if not (request.form.get("symbol")):
            return apology("Must put in some Symbol")
        else:
            stockinformation= lookup(request.form.get("symbol"))
            if (stockinformation!=None):
                return render_template("quoted.html", stockinformation=stockinformation)
            else:
                return apology("Couldn't find the stock according to your Symbol")
    else:
        return render_template("quote.html")
    #return redirect to a page displaying the information from lookup

    return apology("TODO")


@app.route("/register", methods=["GET", "POST"])
def register():

    """Register user"""
    # Forget any user_id
    session.clear()

    if request.method == "POST":
        #check if username and passwords are provided and match
        if not request.form.get("username"):
                return apology("must provide username", 403)
        elif not request.form.get("password"):
                return apology("must provide password", 403)
        elif (request.form.get("password")!=request.form.get("password-verification")):
                return apology("passwords do not match", 403)

        #encrypt password
        hash = generate_password_hash(request.form.get("password"), method='pbkdf2:sha256', salt_length=8)
        print(hash)

        #write new user in db
        result=db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)", {"username":request.form.get("username"), "hash":hash})
        db.commit()
        #if username already exists:
        if not (result):
            return apology("username already exists", 403)

        # Remember which user has logged in
        session["user_id"] = result

        #log in new user
        return redirect("/")

    else:
        return render_template("register.html")
    return apology("TODO")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    if request.method == "POST":
        userid=session["user_id"]
        symbol=request.form.get("symbol")
        try:
            shares = int(request.form.get("shares"))
            if shares < 0:
                return apology("Shares must be positive integer")
        except:
            return apology("Shares must be positive integer")
        operation="sell"
        price=lookup(symbol)["price"]*shares
        balance=db.execute("SELECT cash FROM users WHERE id = :id", id=userid)[0]["cash"]
        """Sell shares of stock"""
        rows=db.execute("SELECT shares FROM 'portfolio' WHERE id = :id AND symbol= :symbol", id=userid, symbol=symbol)
        #no such Stocks in portfolio
        print("1")
        if(len(rows)!=1):

            return apology("You don't own what you want to sell")
        else:
            print("2")
            print(rows[0]['shares'])
            #too few Stocks in portfolio
            if (int(shares)>rows[0]['shares']):
                return apology("You want to sell more than you own")
            #update balance and shares
            else:
                #update balance
                db.execute("UPDATE users SET cash= :balance + :price WHERE id = ':id'", id=userid, price=price, balance=balance)
                #update history
                db.execute("INSERT INTO history (id, operation, symbol, shares) VALUES(':id', :operation, :symbol, ':shares'); ", id=userid, operation=operation, symbol=symbol, shares=shares)

                #delete row if no shares are left
                if(int(shares)==rows[0]['shares']):
                   db.execute("DELETE FROM portfolio WHERE id = :id AND symbol= :symbol;", id=userid, symbol=symbol)
                #otherwise update portfolio
                else:
                    db.execute("UPDATE portfolio SET shares = shares - :shares WHERE id = :id AND symbol= :symbol;", id=userid, symbol=symbol, shares=shares)

        return redirect("/")

    else:
        return render_template("sell.html")


def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
