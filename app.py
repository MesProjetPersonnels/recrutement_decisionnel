from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import pickle
import secrets

model = pickle.load(open('recruitment_model.pkl', 'rb'))

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Configure the User class
class User(UserMixin):
    def __init__(self, id, username, password, role):
        self.id = id
        self.username = username
        self.password = password
        self.role = role

@login_manager.user_loader
def load_user(user_id):
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user_data = cursor.fetchone()
    cursor.close()
    db.close()
    if user_data:
        return User(user_data[0], user_data[1], user_data[2], user_data[3])
    return None

def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='recrutement_universites'
    )

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user_data = cursor.fetchone()
        cursor.close()
        db.close()
        if user_data and check_password_hash(user_data[2], password):
            user = User(user_data[0], user_data[1], user_data[2], user_data[3])
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/vacances')
def vacances():
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM vacances")
    data = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template('vacances.html', data=data)

@app.route('/demande', methods=['GET', 'POST'])
def demande():
    if request.method == 'POST':
        nom = request.form['nom']
        prenom = request.form['prenom']
        email = request.form['email']
        disponibilite = float(request.form.get('disponibilite', 0))
        distinction = float(request.form.get('distinction', 0))
        moyenne = float(request.form['moyenne'])
        vacance_id = request.form['vacance_id']
        probability = request.form.get('probability', 0)
        try:
            probability = float(probability)
        except ValueError:
            probability = 0  # Gérer les probabilités manquantes ou invalides
        cv = request.files['cv'].read()
        releve_cotes = request.files['releve_cotes'].read()

        db = get_db_connection()
        cursor = db.cursor()

        # Insérer les informations du candidat avec son score
        cursor.execute("INSERT INTO candidats (nom, prenom, email, disponibilite, distinction, moyenne, score) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                       (nom, prenom, email, disponibilite, distinction, moyenne, probability))
        candidat_id = cursor.lastrowid

        # Insérer la demande d'emploi
        cursor.execute("INSERT INTO demandes (candidat_id, vacance_id, cv, releve_cotes, date_soumission) VALUES (%s, %s, %s, %s, CURDATE())",
                       (candidat_id, vacance_id, cv, releve_cotes))

        db.commit()
        cursor.close()
        db.close()

        # Afficher le message de succès et la probabilité
        return render_template('success.html', probability=probability)

    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM vacances")
    vacances = cursor.fetchall()
    cursor.close()
    db.close()

    return render_template('demande.html', vacances=vacances)

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json(force=True) 
    prediction = model.predict_proba([[ data['disponibilite'], 
                data['distinction'],
                data['moyenne'] 
                ]]) 
    output = {'probability': prediction[0][1]} 
    return jsonify(output)

def predict_probability(disponibilite, distinction, moyenne):
    # Exemple de fonction de prédiction basée sur des poids fictifs
    return 0.2 * disponibilite + 0.3 * distinction + 0.5 * moyenne


@app.route('/candidats')
@login_required
def candidats():
    if not current_user.is_authenticated or current_user.role != 'admin':
        return redirect(url_for('index'))
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("SELECT nom, prenom, score FROM candidats")
    candidats = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template('candidats.html', candidats=candidats)

@app.route('/add_vacance', methods=['GET', 'POST'])
@login_required
def add_vacance():
    if not current_user.is_authenticated or current_user.role != 'admin':
        return redirect(url_for('index'))
    if request.method == 'POST':
        # Add code for processing add_vacance
        pass
    return render_template('add_vacance.html')

@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')


        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                       (username, hashed_password, role))
        db.commit()
        cursor.close()
        db.close()

        flash('Utilisateur ajouté avec succès!')
        return redirect(url_for('index'))

    return render_template('add_user.html')


if __name__ == '__main__':
    app.run(debug=True)
