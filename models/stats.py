import pandas as pd
import numpy as np
import os


class IPLStats:
    def __init__(self):
        self.matches_df = None
        self.deliveries_df = None
        self._load_data()

    def _load_data(self):
        match_paths = [
            'data/matches.csv', 'data/IPL Matches 2008-2022.csv',
            'data/ipl_matches.csv', 'data/matches_ipl.csv'
        ]
        for p in match_paths:
            if os.path.exists(p):
                self.matches_df = pd.read_csv(p)
                self.matches_df.columns = [c.lower().replace(' ', '_') for c in self.matches_df.columns]
                break

        delivery_paths = [
            'data/deliveries.csv', 'data/IPL Ball-by-Ball 2008-2022.csv',
            'data/ipl_deliveries.csv', 'data/ball_by_ball.csv'
        ]
        for p in delivery_paths:
            if os.path.exists(p):
                self.deliveries_df = pd.read_csv(p)
                self.deliveries_df.columns = [c.lower().replace(' ', '_') for c in self.deliveries_df.columns]
                break

        if self.matches_df is None:
            self.matches_df = self._synthetic_matches()
        if self.deliveries_df is None:
            self.deliveries_df = self._synthetic_deliveries()

    def _synthetic_matches(self):
        np.random.seed(42)
        teams = [
            'Mumbai Indians', 'Chennai Super Kings', 'Royal Challengers Bangalore',
            'Kolkata Knight Riders', 'Delhi Capitals', 'Rajasthan Royals',
            'Punjab Kings', 'Sunrisers Hyderabad', 'Gujarat Titans', 'Lucknow Super Giants'
        ]
        venues = [
            'Wankhede Stadium', 'MA Chidambaram Stadium', 'Eden Gardens',
            'Feroz Shah Kotla', 'Sawai Mansingh Stadium', 'Rajiv Gandhi International Stadium',
            'Punjab Cricket Association Stadium', 'Narendra Modi Stadium'
        ]
        players = [
            'Virat Kohli', 'Rohit Sharma', 'MS Dhoni', 'AB de Villiers', 'Chris Gayle',
            'Suresh Raina', 'David Warner', 'Kane Williamson', 'KL Rahul', 'Hardik Pandya',
            'Jasprit Bumrah', 'Lasith Malinga', 'Harbhajan Singh', 'Ravindra Jadeja'
        ]
        records = []
        match_id = 1
        for season in range(2008, 2024):
            for _ in range(60):
                t1, t2 = np.random.choice(teams, 2, replace=False)
                venue = np.random.choice(venues)
                toss_win = np.random.choice([t1, t2])
                toss_dec = np.random.choice(['bat', 'field'])
                winner = t1 if np.random.random() > 0.45 else t2
                margin_type = np.random.choice(['runs', 'wickets'])
                margin = np.random.randint(1, 10) if margin_type == 'wickets' else np.random.randint(1, 100)
                records.append({
                    'id': match_id, 'season': season, 'team1': t1, 'team2': t2,
                    'venue': venue, 'toss_winner': toss_win, 'toss_decision': toss_dec,
                    'winner': winner, 'result': margin_type, 'result_margin': margin,
                    'player_of_match': np.random.choice(players),
                    'city': venue.split(' ')[0]
                })
                match_id += 1
        return pd.DataFrame(records)

    def _synthetic_deliveries(self):
        np.random.seed(0)
        batsmen = [
            'Virat Kohli', 'Rohit Sharma', 'MS Dhoni', 'AB de Villiers', 'Chris Gayle',
            'Suresh Raina', 'David Warner', 'KL Rahul', 'Hardik Pandya', 'Shikhar Dhawan',
            'Gautam Gambhir', 'Shane Watson', 'Yuvraj Singh', 'Brendon McCullum'
        ]
        bowlers = [
            'Jasprit Bumrah', 'Lasith Malinga', 'Harbhajan Singh', 'Ravindra Jadeja',
            'Amit Mishra', 'Dwayne Bravo', 'Sunil Narine', 'Yuzvendra Chahal',
            'Mohammed Shami', 'Bhuvneshwar Kumar'
        ]
        records = []
        for match_id in range(1, 961):
            n_balls = np.random.randint(110, 130)
            for ball in range(n_balls):
                batsman = np.random.choice(batsmen)
                bowler = np.random.choice(bowlers)
                runs = np.random.choice([0, 1, 2, 3, 4, 6], p=[0.35, 0.30, 0.12, 0.03, 0.12, 0.08])
                is_wicket = 1 if np.random.random() < 0.045 else 0
                records.append({
                    'match_id': match_id,
                    'batsman': batsman,
                    'bowler': bowler,
                    'batsman_runs': runs,
                    'total_runs': runs,
                    'is_wicket': is_wicket,
                    'dismissal_kind': 'caught' if is_wicket else None,
                    'inning': 1 if ball < n_balls // 2 else 2
                })
        return pd.DataFrame(records)

    def head_to_head(self, team1, team2):
        df = self.matches_df
        h2h = df[((df['team1'] == team1) & (df['team2'] == team2)) |
                  ((df['team1'] == team2) & (df['team2'] == team1))].copy()
        total = len(h2h)
        if total == 0:
            return {'total': 0, 'matches': []}
        t1_wins = int((h2h['winner'] == team1).sum())
        t2_wins = int((h2h['winner'] == team2).sum())
        by_season = h2h.groupby('season')['winner'].apply(list).to_dict()

        # Season-wise win count
        season_data = []
        for season in sorted(by_season.keys()):
            winners = by_season[season]
            season_data.append({
                'season': int(season),
                'team1_wins': sum(1 for w in winners if w == team1),
                'team2_wins': sum(1 for w in winners if w == team2)
            })

        return {
            'total': total,
            'team1_wins': t1_wins,
            'team2_wins': t2_wins,
            'team1_pct': round(t1_wins / total * 100, 1),
            'team2_pct': round(t2_wins / total * 100, 1),
            'season_data': season_data
        }

    def team_stats(self, team_name):
        df = self.matches_df
        team_matches = df[(df['team1'] == team_name) | (df['team2'] == team_name)]
        total = len(team_matches)
        wins = int((team_matches['winner'] == team_name).sum())
        losses = total - wins
        win_rate = round(wins / max(total, 1) * 100, 1)

        # Season-wise performance
        team_matches = team_matches.copy()
        def row_result(row):
            return 1 if row['winner'] == team_name else 0
        team_matches['won'] = team_matches.apply(row_result, axis=1)
        season_perf = team_matches.groupby('season').agg(
            matches=('won', 'count'),
            wins=('won', 'sum')
        ).reset_index()
        season_perf['win_rate'] = (season_perf['wins'] / season_perf['matches'] * 100).round(1)

        titles = 0
        if 'season' in df.columns:
            for season in df['season'].unique():
                season_df = df[df['season'] == season]
                # Last match of season (crude)
                last_match = season_df.iloc[-1] if len(season_df) > 0 else None
                if last_match is not None and last_match.get('winner') == team_name:
                    titles += 1

        return {
            'team': team_name,
            'total_matches': total,
            'wins': wins,
            'losses': losses,
            'win_rate': win_rate,
            'titles': titles,
            'season_performance': season_perf.to_dict(orient='records')
        }

    def season_stats(self):
        df = self.matches_df
        seasons = sorted(df['season'].unique())
        results = []
        for s in seasons:
            sdf = df[df['season'] == s]
            winner_counts = sdf['winner'].value_counts().to_dict()
            champion = max(winner_counts, key=winner_counts.get) if winner_counts else 'N/A'
            results.append({
                'season': int(s),
                'matches': len(sdf),
                'champion': champion,
                'teams': list(set(sdf['team1'].tolist() + sdf['team2'].tolist()))
            })
        return results

    def top_players(self):
        df = self.deliveries_df

        # Top batsmen by runs
        batsmen = df.groupby('batsman')['batsman_runs'].sum().sort_values(ascending=False).head(10)
        batsmen_data = [{'name': k, 'runs': int(v)} for k, v in batsmen.items()]

        # Top bowlers by wickets
        wickets_df = df[df['is_wicket'] == 1]
        # Exclude run-outs
        if 'dismissal_kind' in wickets_df.columns:
            wickets_df = wickets_df[wickets_df['dismissal_kind'] != 'run out']
        bowlers = wickets_df.groupby('bowler')['is_wicket'].sum().sort_values(ascending=False).head(10)
        bowlers_data = [{'name': k, 'wickets': int(v)} for k, v in bowlers.items()]

        # Strike rates
        balls = df.groupby('batsman')['batsman_runs'].count()
        runs = df.groupby('batsman')['batsman_runs'].sum()
        sr = ((runs / balls) * 100).sort_values(ascending=False)
        sr_data = [{'name': k, 'strike_rate': round(v, 1)} for k, v in sr.head(10).items()]

        return {
            'top_batsmen': batsmen_data,
            'top_bowlers': bowlers_data,
            'top_strike_rates': sr_data
        }

    def venue_stats(self, venue):
        df = self.matches_df
        vdf = df[df['venue'] == venue]
        total = len(vdf)
        if total == 0:
            return {'venue': venue, 'total': 0}
        toss_bat_wins = len(vdf[(vdf['toss_decision'] == 'bat') & (vdf['winner'] == vdf['toss_winner'])])
        toss_field_wins = len(vdf[(vdf['toss_decision'] == 'field') & (vdf['winner'] == vdf['toss_winner'])])
        winner_counts = vdf['winner'].value_counts().head(5).to_dict()
        return {
            'venue': venue,
            'total_matches': total,
            'bat_first_toss_win_pct': round(toss_bat_wins / max(total, 1) * 100, 1),
            'field_first_toss_win_pct': round(toss_field_wins / max(total, 1) * 100, 1),
            'top_teams': [{'team': k, 'wins': v} for k, v in winner_counts.items()]
        }
