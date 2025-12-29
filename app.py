import os
import dash
import authenticator
from pages import editor, viewer
from data_handler import init_database
from dash import html, dcc, Input, Output, State, Dash
import flask
import dash_bootstrap_components as dbc
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
import pyotp

init_database()

# --- CONFIGURATION ---
server = flask.Flask(__name__)
server.secret_key = 'remplacez_ceci_par_une_cle_tres_secrete'

# --- FLASK LOGIN ---
login_manager = LoginManager()
login_manager.init_app(server)
login_manager.login_view = "/login"

class User(UserMixin):
    def __init__(self, id): self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id) if user_id == authenticator.get_user()[0] else None

# --- APP DASH ---
app = dash.Dash(__name__, server=server, suppress_callback_exceptions=True)

# Layout de base
app.layout = html.Div([
    dcc.Location(id='url', refresh=True),
    html.Div(id='page-content')
])

home_layout = html.Div([
    html.H1("Tableau de bord Raspberry Pi"),
    html.P("Bienvenue dans votre interface de contrôle centralisée."),
    html.Ul([
        html.Li("Access to Edition to add new ideas/notes."),
        html.Li("Visualize database and navigate into ideas."),
    ])
])

# Formulaire de Connexion
login_layout = html.Div([
    html.H2("Connexion Sécurisée"),
    dcc.Input(id='email', type='text', placeholder='Email'),
    dcc.Input(id='pwd', type='password', placeholder='Mot de passe'),
    dcc.Input(id='otp', type='text', placeholder='Code Google Authenticator (6 chiffres)'),
    html.Button('Se connecter', id='login-button', n_clicks=0),
    html.Div(id='login-error', style={'color': 'red'})
], style={'textAlign': 'center', 'marginTop': '100px'})

# Barre de navigation (visible uniquement si connecté)
def navbar():
    return html.Nav([
        dcc.Link('Home', href='/home', className="nav-link"),
        dcc.Link('Add ideas', href='/edit', className="nav-link"),
        dcc.Link('Vizualisation', href='/viz', className="nav-link"),
        html.A('Sign out', href='/logout', className="nav-link logout")
    ], className="navbar")

app.layout = html.Div([
    dcc.Location(id='url', refresh=True),
    html.Div(id='navbar-container'),
    html.Div(id='page-content', className="container")
])

# --- CALLBACKS DE NAVIGATION ---
# Router principal
@app.callback(
    [Output('page-content', 'children'), Output('navbar-container', 'children')],
    [Input('url', 'pathname')]
)
def display_page(pathname):
    if not current_user.is_authenticated:
        return login_layout, None
    
    nav = navbar()
    if pathname == '/edit': return editor.layout, nav
    if pathname == '/viz': return viewer.layout, nav
    return home_layout, nav # Par défaut : Accueil

# Logique de vérification Login + OTP
@app.callback(
    [Output('url', 'pathname'), Output('login-error', 'children')],
    [Input('login-button', 'n_clicks')],
    [State('email', 'value'), State('pwd', 'value'), State('otp', 'value')]
)
def auth_login(n_clicks, email: str, pwd: str, otp: str):
    if n_clicks > 0:
        user_email, user_pwd = authenticator.get_user()
        if email == user_email and pwd == user_pwd:
            # Vérification du code Google Authenticator
            totp = pyotp.TOTP(authenticator.get_otp_secret())
            if totp.verify(otp):
                print("auth successful")
                login_user(User(email))
                return '/', ''
            else:
                print("Code OTP invalide")
                return dash.no_update, "Code OTP invalide"
        return dash.no_update, "Identifiants incorrects"
    return dash.no_update, ""

# Route Flask pour la déconnexion
@server.route('/logout')
def logout():
    logout_user()
    return flask.redirect('/login')

# if __name__ == '__main__':
#     app.run_server(host='0.0.0.0', port=8050, debug=False)

if __name__ == "__main__":
    dir_path = os.path.dirname(os.path.realpath(__file__))
    app.run(debug=True)
