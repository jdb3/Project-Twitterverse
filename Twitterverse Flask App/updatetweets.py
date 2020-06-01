import GetOldTweets3 as got
from textblob import TextBlob
import pandas as pd
import numpy as np
import datetime
import time
import arrow
import warnings
import matplotlib
import matplotlib.pyplot as plt
import unicodedata
import time
from flask import Flask, render_template, redirect
from flask_pymongo import PyMongo
import pymongo
from yahoo_fin import stock_info as si
import yfinance as yf
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import re as re




def refresh():

    today = (datetime.datetime.today() + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    lastweek = (datetime.datetime.today() - datetime.timedelta(days=7)).strftime('%Y-%m-%d')
    tweetCriteria = got.manager.TweetCriteria().setUsername("realDonaldTrump")\
                                           .setSince(lastweek)\
                                           .setUntil(today)

    tweets = got.manager.TweetManager.getTweets(tweetCriteria)

    rows = []
    for tweet in tweets:
        rows.append([tweet.id, tweet.permalink, tweet.username, tweet.to, tweet.text, tweet.date, tweet.retweets, tweet.favorites, tweet.mentions, tweet.hashtags, tweet.geo])

    df = pd.DataFrame(rows, columns=["id", "permalink", "username", "to", "text", "date", "retweets", "favorites", "mentions", "hashtags", "geo"])
    
    def findmarketdate(date):
        if (date.strftime('%A') in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]) and (int(date.strftime('%H')) < 20):
            return date.strftime('%Y-%m-%d')
        elif (date.strftime('%A') in ["Monday", "Tuesday", "Wednesday", "Thursday"]) and (int(date.strftime('%H')) > 20):
            return (date + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        elif (date.strftime('%A') == "Friday") and (int(date.strftime('%H')) > 20):
            return (date + datetime.timedelta(days=3)).strftime('%Y-%m-%d')
        elif (date.strftime('%A') == "Saturday"):
            return (date + datetime.timedelta(days=2)).strftime('%Y-%m-%d')
        else:
            return (date + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        

    def getpolarity(tweet):
        analysis = TextBlob(tweet)
        return round(analysis.sentiment.polarity,2)
    def getposneg(sentiment):
        if sentiment > 0:
            return "green"
        elif sentiment < 0:
            return "red"
        else:
            return "black"
    def getsubjectivity(tweet):
        analysis = TextBlob(tweet)
        return round(analysis.sentiment.subjectivity,2)
    def clean_tweet(tweet):
        return ' '.join(re.sub('(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)', ' ', tweet).split())
    def vadercompound(tweet):
        analyzer = SentimentIntensityAnalyzer()
        return round(analyzer.polarity_scores(tweet)["compound"],2)

    df['marketdate'] = df['date'].apply(findmarketdate)
    df["Text"] = df['text'].apply(clean_tweet)
    df['Text'] = df['Text'].astype(str)
    df['polarity'] = df['text'].apply(getpolarity)
    df['subjectivity'] = df['text'].apply(getsubjectivity)
    df['compoundvader'] = df['Text'].apply(vadercompound)
    df = df.loc[df['text'] != '']


    datelist = []
    for x in range(0,7):
        day = (datetime.datetime.today() - datetime.timedelta(days=x))
        if (day.strftime('%A') in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]):
            datelist.append(day.strftime('%Y-%m-%d'))
    
    marketdict = {}
    tickerdict = {'^DJI': 'Dow30', '^IXIC': 'NASDAQ', '^GSPC': 'SP500', '^VIX': 'CBOEVolatilityIndex', '^RUT': 'Russell2000'}
    #timedifference = (4/24)
    now = (datetime.datetime.today() - datetime.timedelta(days=0)).strftime('%m-%d-%Y %I:%M %p')

    for tick in tickerdict:
        #get data on this ticker , end=datelist[0]
        tickerData = yf.Ticker(tick)
        #get the historical prices for this ticker
        tickerDf = tickerData.history(period='1d', start= datelist[4])
        tickerDf = tickerDf.sort_values('Date', ascending=False)
        tickerDf['Delta'] = round((tickerDf['Close'] - tickerDf['Open']),2)
        marketdict[tickerdict[tick]] = tickerDf.reset_index()

    dicts = {}


    for i in datelist:
        tweets = {}
        stock = {}
        dataframe = df.loc[df['marketdate'] == i]
        #print(dataframe)
        #stockdf = tickerDf.loc[tickerDf['Date'] == i]
        
        tweetlist = []
        retweetlist = []
        favoritelist = []
        linklist = []
        polaritylist = []
        subjectivitylist = []
        vadercomplist = []
        for row in dataframe['text']:
            tweetlist.append(row)
            tweets['Tweets'] = tweetlist
        for row in dataframe['retweets']:
            retweetlist.append(row)
            tweets['Retweets'] = retweetlist
        for row in dataframe['favorites']:
            favoritelist.append(row)
            tweets['Favorites'] = favoritelist
        for row in dataframe['permalink']:
            linklist.append(row)
            tweets['Link'] = linklist
        for row in dataframe['polarity']:
            polaritylist.append(row)
            tweets['Polarity'] = polaritylist
        for row in dataframe['subjectivity']:
            subjectivitylist.append(row)
            tweets['Subjectivity'] = subjectivitylist
        for row in dataframe['compoundvader']:
            vadercomplist.append(row)
            tweets['Vader_Comp'] = vadercomplist
        
        
        for ticker in marketdict:
            tickerDF = marketdict[ticker]
            #marketdict[ticker] = tickerDF
            stockdf = tickerDF.loc[tickerDF['Date'] == i]
            
            for row in stockdf['Open']:
                stock[f'{ticker}_Open'] = row
            for row in stockdf['Close']:
                stock[f'{ticker}_Close'] = row
            for row in stockdf['Delta']:
                stock[f'{ticker}_Delta'] = row
            for row in stockdf['Delta']:
                if row > 0:
                    stock[f'{ticker}goodbad'] = "green"
                elif row < 0:
                    stock[f'{ticker}goodbad'] = "red"
                else:
                    stock[f'{ticker}goodbad'] = "black"
                    
        
        dicts[f'Day{datelist.index(i)}'] = [i, tweets, stock]
        
    dicts['TimeStamp'] = now

    conn = 'mongodb+srv://mytweepyapp:Password@twitterverse-z9192.mongodb.net/test?retryWrites=true&w=majority'
    client = pymongo.MongoClient(conn)

    # # Define database and collection
    db = client.ThisWeekTweets
    collection = db.trumptweets

    collection.drop()

    #data_dict = df.to_dict(orient='list')
    # insert new data into collection
    collection.insert_one(dicts)

    CEOList = ['@SteveForbesCEO', '@marcuslemonis', '@elonmusk']
    CEODict = {'@SteveForbesCEO': 'BSE', '@marcuslemonis': 'CWH', '@elonmusk': 'TSLA'}

    othertweetdict = {}
    for CEO in CEOList:
        othertweetCriteria = got.manager.TweetCriteria().setUsername(CEO)\
                                            .setSince(lastweek)\
                                            .setUntil(today)
        othertweets = got.manager.TweetManager.getTweets(othertweetCriteria)
        rows = []
        for tweet in othertweets:
            rows.append([tweet.id, tweet.permalink, tweet.username, tweet.to, tweet.text, tweet.date, tweet.retweets, tweet.favorites, tweet.mentions, tweet.hashtags, tweet.geo])
        odf = pd.DataFrame(rows, columns=["id", "permalink", "username", "to", "text", "date", "retweets", "favorites", "mentions", "hashtags", "geo"])
        #odf['tweetdate'] = odf['date'].apply(getdate)
        #odf['tweetdayofweek'] = odf['date'].apply(getdayofweek)
        #odf['tweethour'] = odf['date'].apply(gethour)
        odf['marketdate'] = odf['date'].apply(findmarketdate)
        odf['polarity'] = odf['text'].apply(getpolarity)
        odf['subjectivity'] = odf['text'].apply(getsubjectivity)
        odf["Text"] = odf['text'].apply(clean_tweet)
        odf['Text'] = odf['Text'].astype(str)
        odf['compoundvader'] = odf['Text'].apply(vadercompound)
        odf = odf.loc[odf['text'] != '']
        othertweetdict[CEO] = odf.reset_index()

    othermarketdict = {}

    for CEO in CEODict:
        #get data on this ticker , end=datelist[0]
        tickerData = yf.Ticker(CEODict[CEO])
        #get the historical prices for this ticker
        tickerDf = tickerData.history(period='1d', start= datelist[4])
        tickerDf = tickerDf.sort_values('Date', ascending=False)
        tickerDf['Delta'] = round((tickerDf['Close'] - tickerDf['Open']),2)
        tickerDf = tickerDf.reset_index()
        tickerDf = tickerDf.rename(columns={'Date': 'marketdate'})
        #tickerDf['marketdate'] = tickerDf['Date']
        othermarketdict[CEO] = tickerDf

    otherdicts = {}
    CEOS = ['SteveForbesCEO', 'marcuslemonis', 'elonmusk']


    for i in datelist:
        tweets = {}
        stock = {}
        
        #print(dataframe)
        #stockdf = tickerDf.loc[tickerDf['Date'] == i]
        for CEO in CEODict:
            dataframe = othertweetdict[CEO].loc[othertweetdict[CEO]['marketdate'] == i]
            tweetlist = []
            retweetlist = []
            favoritelist = []
            linklist = []
            polaritylist = []
            subjectivitylist = []
            vadercomplist = []
            for row in dataframe['text']:
                tweetlist.append(row)
                tweets[f'{CEODict[CEO]}Tweets'] = tweetlist
            for row in dataframe['retweets']:
                retweetlist.append(row)
                tweets[f'{CEODict[CEO]}Retweets'] = retweetlist
            for row in dataframe['favorites']:
                favoritelist.append(row)
                tweets[f'{CEODict[CEO]}Favorites'] = favoritelist
            for row in dataframe['permalink']:
                linklist.append(row)
                tweets[f'{CEODict[CEO]}Link'] = linklist
            for row in dataframe['polarity']:
                polaritylist.append(row)
                tweets[f'{CEODict[CEO]}Polarity'] = polaritylist
            for row in dataframe['subjectivity']:
                subjectivitylist.append(row)
                tweets[f'{CEODict[CEO]}Subjectivity'] = subjectivitylist
            for row in dataframe['compoundvader']:
                vadercomplist.append(row)
                tweets[f'{CEODict[CEO]}Vader_Comp'] = vadercomplist


        for ticker in othermarketdict:
            tickerDF = othermarketdict[ticker]
            #marketdict[ticker] = tickerDF
            stockdf = tickerDF.loc[tickerDF['marketdate'] == i]

            for row in stockdf['Open']:
                stock[f'{CEODict[ticker]}_Open'] = row
            for row in stockdf['Close']:
                stock[f'{CEODict[ticker]}_Close'] = row
            for row in stockdf['Delta']:
                stock[f'{CEODict[ticker]}_Delta'] = row
            for row in stockdf['Delta']:
                if row > 0:
                    stock[f'{CEODict[ticker]}goodbad'] = "green"
                elif row < 0:
                    stock[f'{CEODict[ticker]}goodbad'] = "red"
                else:
                    stock[f'{CEODict[ticker]}goodbad'] = "black"

        otherdicts[f'Day{datelist.index(i)}'] = [i, tweets, stock]
        
    otherdicts['TimeStamp'] = now

        # # Define database and collection
    db = client.ThisWeekTweets
    collection = db.othertweets

    # Clear previous data in collection
    collection.drop()

        # insert new data into collection
    collection.insert_one(otherdicts)

    grouped = df.groupby('marketdate').mean().round(3)
    grouped = grouped.sort_values('marketdate', ascending=False)
    grouped['posneg'] = grouped['compoundvader'].apply(getposneg)
    grouped = grouped.reset_index()
    grouped = grouped.to_dict(orient='list')

    db = client.ThisWeekTweets
    collection = db.groupedbydate

    # Clear previous data in collection
    collection.drop()

    #data_dict = df.to_dict(orient='list')
    # insert new data into collection
    collection.insert_one(grouped)

    othergroupeddict = {}
    for CEO in CEOList:
        ogrouped = othertweetdict[CEO].groupby('marketdate').mean().round(3)
        ogrouped = ogrouped.sort_values('marketdate', ascending=False)
        ogrouped['posneg'] = ogrouped['compoundvader'].apply(getposneg)
        ogrouped = ogrouped.reset_index()
        ogrouped = ogrouped.to_dict(orient='list')
        othergroupeddict[CEO] = ogrouped

    db = client.ThisWeekTweets
    collection = db.groupedbydate

    # Clear previous data in collection
    #collection.drop()

    #data_dict = df.to_dict(orient='list')
    # insert new data into collection
    collection.insert_one(othergroupeddict)








    

    return dicts




 