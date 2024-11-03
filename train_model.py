import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
import pickle

# Charger les données
data = pd.read_csv('candidats.csv', sep=';')

# Préparer les données
X = data[['disponibilite', 'distinction', 'moyenne']].applymap(lambda x: x.replace(',', '.') if isinstance(x, str) else x).astype(float)
y = data['recrute']

# Diviser les données en ensembles d'entraînement et de test
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Entraîner le modèle
model = LogisticRegression()
model.fit(X_train, y_train)

# Sauvegarder le modèle
pickle.dump(model, open('recruitment_model.pkl', 'wb'))
