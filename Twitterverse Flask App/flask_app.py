from flask import Flask, render_template, request, redirect
from flask_pymongo import PyMongo
import updatetweets

app = Flask(__name__)

#app.config["MONGO_URI"] = "mongodb+srv://mytweepyapp:<password>@twitterverse-z9192.mongodb.net/test?retryWrites=true&w=majority"
app.config["MONGO_URI"] = "mongodb://localhost:27017/ThisWeekTweets"
mongo = PyMongo(app)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/summary")
def summary():
    return render_template("intro.html")

@app.route("/predictions")
def predictions():
    tweetdata = mongo.db.trumptweets.find_one()
    aggtweets = mongo.db.groupedbydate.find_one()
    return render_template("predictions.html", tweets = tweetdata, aggtweets = aggtweets)

@app.route("/visuals")
def visuals():
    return render_template("visuals.html")

@app.route("/wordcloud")
def wordcloud():
    return render_template("wordcloud.html")

@app.route("/correlation")
def correlation():
    return render_template("correlation.html")

@app.route("/casestudy")
def casestudy():
    return render_template("casestudy.html")

@app.route("/machinelearning")
def machinelearning():
    return render_template("machinelearning.html")

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