from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
import os
import json
from models.predictor import IPLPredictor
from models.stats import IPLStats

app = Flask(__name__)

# Initialize models and stats
predictor = IPLPredictor()
stats_engine = IPLStats()

@app.route('/')
def index():
    teams = predictor.get_teams()
    venues = predictor.get_venues()
    return render_template('index.html', teams=teams, venues=venues)

@app.route('/api/predict', methods=['POST'])
def predict():
    data = request.get_json()
    team1 = data.get('team1')
    team2 = data.get('team2')
    venue = data.get('venue')
    toss_winner = data.get('toss_winner')
    toss_decision = data.get('toss_decision')

    result = predictor.predict(team1, team2, venue, toss_winner, toss_decision)
    return jsonify(result)

@app.route('/api/head_to_head', methods=['POST'])
def head_to_head():
    data = request.get_json()
    team1 = data.get('team1')
    team2 = data.get('team2')
    result = stats_engine.head_to_head(team1, team2)
    return jsonify(result)

@app.route('/api/team_stats/<team_name>')
def team_stats(team_name):
    result = stats_engine.team_stats(team_name)
    return jsonify(result)

@app.route('/api/season_stats')
def season_stats():
    result = stats_engine.season_stats()
    return jsonify(result)

@app.route('/api/top_players')
def top_players():
    result = stats_engine.top_players()
    return jsonify(result)

@app.route('/api/venue_stats/<venue>')
def venue_stats(venue):
    result = stats_engine.venue_stats(venue)
    return jsonify(result)

@app.route('/api/teams')
def get_teams():
    return jsonify(predictor.get_teams())

if __name__ == '__main__':
    print("Training models...")
    predictor.train()
    print("Models trained! Starting server...")
    app.run(debug=True, port=5000)
