import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import os
import warnings
warnings.filterwarnings('ignore')

class IPLPredictor:
    def __init__(self):
        self.lr_model = LogisticRegression(max_iter=1000, random_state=42)
        self.rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.team_encoder = LabelEncoder()
        self.venue_encoder = LabelEncoder()
        self.toss_encoder = LabelEncoder()
        self.is_trained = False
        self.teams = []
        self.venues = []
        self.df = None
        self._load_data()

    def _load_data(self):
        """Load IPL matches dataset"""
        # Try common dataset paths
        paths = [
            'data/matches.csv',
            'data/IPL Matches 2008-2022.csv',
            'data/ipl_matches.csv',
            'data/matches_ipl.csv',
        ]
        for path in paths:
            if os.path.exists(path):
                self.df = pd.read_csv(path)
                print(f"Loaded data from {path}, shape: {self.df.shape}")
                self._preprocess()
                return

        # Generate synthetic data if no dataset found
        print("No dataset found, generating synthetic IPL data...")
        self.df = self._generate_synthetic_data()
        self._preprocess()

    def _generate_synthetic_data(self):
        """Generate realistic synthetic IPL data"""
        np.random.seed(42)
        teams = [
            'Mumbai Indians', 'Chennai Super Kings', 'Royal Challengers Bangalore',
            'Kolkata Knight Riders', 'Delhi Capitals', 'Rajasthan Royals',
            'Punjab Kings', 'Sunrisers Hyderabad', 'Gujarat Titans', 'Lucknow Super Giants'
        ]
        venues = [
            'Wankhede Stadium', 'MA Chidambaram Stadium', 'Eden Gardens',
            'Feroz Shah Kotla', 'Sawai Mansingh Stadium', 'Rajiv Gandhi International Stadium',
            'Punjab Cricket Association Stadium', 'Narendra Modi Stadium', 'Ekana Cricket Stadium'
        ]
        toss_decisions = ['bat', 'field']
        records = []
        for season in range(2008, 2024):
            for _ in range(60):
                t1, t2 = np.random.choice(teams, 2, replace=False)
                venue = np.random.choice(venues)
                toss_win = np.random.choice([t1, t2])
                toss_dec = np.random.choice(toss_decisions)
                # Bias winner based on toss
                if toss_dec == 'bat':
                    winner = t1 if np.random.random() > 0.45 else t2
                else:
                    winner = toss_win if np.random.random() > 0.4 else (t2 if toss_win == t1 else t1)
                records.append({
                    'season': season,
                    'team1': t1,
                    'team2': t2,
                    'venue': venue,
                    'toss_winner': toss_win,
                    'toss_decision': toss_dec,
                    'winner': winner,
                    'player_of_match': 'Virat Kohli'
                })
        return pd.DataFrame(records)

    def _preprocess(self):
        """Preprocess the dataframe"""
        df = self.df.copy()
        # Standardize column names
        df.columns = [c.lower().replace(' ', '_') for c in df.columns]

        # Handle various column naming conventions
        col_map = {
            'match_winner': 'winner',
            'winning_team': 'winner',
            'toss_decision': 'toss_decision',
        }
        for old, new in col_map.items():
            if old in df.columns and new not in df.columns:
                df.rename(columns={old: new}, inplace=True)

        self.df = df
        all_teams = list(set(df['team1'].dropna().tolist() + df['team2'].dropna().tolist()))
        self.teams = sorted([t for t in all_teams if isinstance(t, str)])
        self.venues = sorted(df['venue'].dropna().unique().tolist())

    def train(self):
        """Train both ML models"""
        df = self.df.dropna(subset=['team1', 'team2', 'venue', 'toss_winner', 'toss_decision', 'winner'])
        df = df[df['winner'].isin(df['team1'].tolist() + df['team2'].tolist())]

        all_teams = list(set(df['team1'].tolist() + df['team2'].tolist() + df['winner'].tolist()))
        self.team_encoder.fit(all_teams)
        self.venue_encoder.fit(df['venue'].unique())
        self.toss_encoder.fit(['bat', 'field'])

        X = self._build_features(df)
        y = (df['winner'] == df['team1']).astype(int)

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        self.lr_model.fit(X_train, y_train)
        self.rf_model.fit(X_train, y_train)

        lr_acc = accuracy_score(y_test, self.lr_model.predict(X_test))
        rf_acc = accuracy_score(y_test, self.rf_model.predict(X_test))
        print(f"Logistic Regression Accuracy: {lr_acc:.3f}")
        print(f"Random Forest Accuracy: {rf_acc:.3f}")

        self.lr_accuracy = round(lr_acc * 100, 1)
        self.rf_accuracy = round(rf_acc * 100, 1)
        self.is_trained = True

    def _build_features(self, df):
        """Build feature matrix"""
        features = pd.DataFrame()
        features['team1_enc'] = self.team_encoder.transform(df['team1'])
        features['team2_enc'] = self.team_encoder.transform(df['team2'])
        try:
            features['venue_enc'] = self.venue_encoder.transform(df['venue'])
        except:
            features['venue_enc'] = 0
        features['toss_winner_is_team1'] = (df['toss_winner'] == df['team1']).astype(int)
        features['toss_decision_enc'] = df['toss_decision'].map({'bat': 1, 'field': 0}).fillna(0)

        # Historical win rates
        win_rates = {}
        for team in self.teams:
            matches = self.df[(self.df['team1'] == team) | (self.df['team2'] == team)]
            wins = self.df[self.df['winner'] == team]
            win_rates[team] = len(wins) / max(len(matches), 1)

        features['team1_winrate'] = df['team1'].map(win_rates).fillna(0.5)
        features['team2_winrate'] = df['team2'].map(win_rates).fillna(0.5)
        features['winrate_diff'] = features['team1_winrate'] - features['team2_winrate']

        return features

    def predict(self, team1, team2, venue, toss_winner, toss_decision):
        """Return prediction probabilities from both models"""
        if not self.is_trained:
            self.train()

        row = pd.DataFrame([{
            'team1': team1, 'team2': team2, 'venue': venue,
            'toss_winner': toss_winner, 'toss_decision': toss_decision
        }])

        try:
            X = self._build_features(row)
        except Exception as e:
            return {'error': str(e)}

        lr_prob = self.lr_model.predict_proba(X)[0]
        rf_prob = self.rf_model.predict_proba(X)[0]

        ensemble_prob = (lr_prob + rf_prob) / 2

        h2h = self._head_to_head_prob(team1, team2)

        return {
            'team1': team1,
            'team2': team2,
            'logistic_regression': {
                'team1_prob': round(lr_prob[1] * 100, 1),
                'team2_prob': round(lr_prob[0] * 100, 1),
                'accuracy': getattr(self, 'lr_accuracy', 'N/A')
            },
            'random_forest': {
                'team1_prob': round(rf_prob[1] * 100, 1),
                'team2_prob': round(rf_prob[0] * 100, 1),
                'accuracy': getattr(self, 'rf_accuracy', 'N/A')
            },
            'ensemble': {
                'team1_prob': round(ensemble_prob[1] * 100, 1),
                'team2_prob': round(ensemble_prob[0] * 100, 1),
            },
            'head_to_head': h2h,
            'predicted_winner': team1 if ensemble_prob[1] > 0.5 else team2
        }

    def _head_to_head_prob(self, team1, team2):
        df = self.df
        h2h = df[((df['team1'] == team1) & (df['team2'] == team2)) |
                  ((df['team1'] == team2) & (df['team2'] == team1))]
        total = len(h2h)
        if total == 0:
            return {'team1_wins': 0, 'team2_wins': 0, 'total': 0}
        t1_wins = len(h2h[h2h['winner'] == team1])
        t2_wins = len(h2h[h2h['winner'] == team2])
        return {
            'team1_wins': t1_wins,
            'team2_wins': t2_wins,
            'total': total,
            'team1_pct': round(t1_wins / total * 100, 1),
            'team2_pct': round(t2_wins / total * 100, 1)
        }

    def get_teams(self):
        return self.teams

    def get_venues(self):
        return self.venues
