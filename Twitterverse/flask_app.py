from flask import Flask, render_template, request, redirect
from flask_pymongo import PyMongo
import updatetweets

app = Flask(__name__)

#app.config["MONGO_URI"] = "mongodb+srv://mytweepyapp:Password@twitterverse-z9192.mongodb.net/test?retryWrites=true&w=majority"
app.config["MONGO_URI"] = "mongodb://localhost:27017/ThisWeekTweets"
mongo = PyMongo(app)

#@app.route("/", methods = ["GET"])

@app.route("/")
def index():
    #tweetdata = mongo.db.trumptweets.find_one()
    return render_template("index.html")

@app.route("/summary")
def summary():
    tweetdata = mongo.db.trumptweets.find_one()
    return render_template("intro.html", tweets = tweetdata)

@app.route("/predictions")
def predictions():
    tweetdata = mongo.db.trumptweets.find_one()
    aggtweets = mongo.db.groupedbydate.find_one()
    return render_template("predictions.html", tweets = tweetdata, aggtweets = aggtweets)

@app.route("/visuals")
def visuals():
    tweetdata = mongo.db.trumptweets.find_one()
    return render_template("visuals.html", tweets = tweetdata)

@app.route("/twitteractivity")
def alltweets():
    tweetdata = mongo.db.trumptweets.find_one()
    othertweetdata = mongo.db.othertweets.find_one()
    accountdata = mongo.db.account_info.find_one()
    return render_template("alltweets.html", tweets = tweetdata, othertweets = othertweetdata, accountdata = accountdata)

@app.route("/refresh")
def refresher():
    tweets = mongo.db.trumptweets
    tweet_data = updatetweets.refresh()
    tweets.update({}, tweet_data, upsert=True)
    return redirect("/twitteractivity", code=302)

@app.route("/musk")
def musk():
    tweetdata = mongo.db.trumptweets.find_one()
    othertweetdata = mongo.db.othertweets.find_one()
    aggtweets = mongo.db.groupedbydate.find()
    return render_template("musk.html", tweets = tweetdata, aggtweets = aggtweets, othertweets = othertweetdata)

@app.route("/cook")
def cook():
    tweetdata = mongo.db.trumptweets.find_one()
    othertweetdata = mongo.db.othertweets.find_one()
    aggtweets = mongo.db.groupedbydate.find()
    return render_template("cook.html", tweets = tweetdata, aggtweets = aggtweets, othertweets = othertweetdata)

@app.route("/ek")
def ek():
    tweetdata = mongo.db.trumptweets.find_one()
    othertweetdata = mongo.db.othertweets.find_one()
    aggtweets = mongo.db.groupedbydate.find()
    return render_template("ek.html", tweets = tweetdata, aggtweets = aggtweets, othertweets = othertweetdata)

@app.route("/forbes")
def forbes():
    tweetdata = mongo.db.trumptweets.find_one()
    othertweetdata = mongo.db.othertweets.find_one()
    aggtweets = mongo.db.groupedbydate.find()
    return render_template("forbes.html", tweets = tweetdata, aggtweets = aggtweets, othertweets = othertweetdata)

@app.route("/lemonis")
def lemonis():
    tweetdata = mongo.db.trumptweets.find_one()
    othertweetdata = mongo.db.othertweets.find_one()
    aggtweets = mongo.db.groupedbydate.find()
    return render_template("lemonis.html", tweets = tweetdata, aggtweets = aggtweets, othertweets = othertweetdata)


if __name__ == "__main__":
    app.run(debug=True)