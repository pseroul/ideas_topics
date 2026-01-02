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
server.secret_key = 'remplacez_ceci par_une_cl3_tres_secrete'

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
app = dash.Dash(__name__, title= "Pierre Seroul", server=server, suppress_callback_exceptions=True)

# Layout de base
app.layout = html.Div([
    dcc.Location(id='url', refresh=True),
    html.Div(id='page-content')
])

home_layout = html.Div([
    html.Div([
        html.H1("Idea manager"),
        html.P("Welcome to the main interface", className="subtitle"),
        html.Div([
            html.Div([
                html.H3("Edition"),
                html.P("Access to Edition to add new ideas/notes."),
                dcc.Link("Open editor", href="/edit", className="btn-secondary")
            ], className="card"),
            html.Div([
                html.H3("Viewer"),
                html.P("Visualize database and navigate into ideas."),
                dcc.Link("Navigate", href="/viz", className="btn-secondary")
            ], className="card"),
        ], className="grid-2")
    ], className="content-container")
])

login_layout = html.Div([
    html.Div([
        html.H2("Secured Access"),
        html.P("Identify yourself to access", className="subtitle"),
        html.Div([
            dcc.Input(id='email', type='text', placeholder='Email', className="form-input"),
            dcc.Input(id='pwd', type='password', placeholder='Mot de passe', className="form-input"),
            dcc.Input(id='otp', type='text', placeholder='Code Google Auth', className="form-input"),
            html.Button('Connect', id='login-button', n_clicks=0, className="btn-primary"),
        ], className="form-stack"), 
        
        html.Div(id='login-error', className="error-msg")
    ], className="card login-card")
], className="page-wrapper center-content")


# Navigation bar, only visible if connected
def navbar():
    return html.Nav([
        dcc.Link('Home', href='/home', className="nav-link"),
        dcc.Link('Add ideas', href='/edit', className="nav-link"),
        dcc.Link('Vizualisation', href='/viz', className="nav-link"),
        html.A('Sign out', href='/logout', className="nav-link logout-btn")
    ], className="navbar")

app.layout = html.Div([
    dcc.Location(id='url', refresh=True),
    html.Div(id='navbar-container'),
    html.Div(id='page-content', className="container")
])


@app.callback(
    [Output('page-content', 'children'), Output('navbar-container', 'children')],
    [Input('url', 'pathname')]
)
def display_page(pathname: str):
    if not current_user.is_authenticated:
        return login_layout, None
    
    nav = navbar()
    if pathname == '/edit': return editor.layout, nav
    if pathname == '/viz': return viewer.layout, nav
    return home_layout, nav 


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


@server.route('/logout')
def logout():
    logout_user()
    return flask.redirect('/login')

if __name__ == "__main__":
    dir_path = os.path.dirname(os.path.realpath(__file__))
    app.run(debug=True)
