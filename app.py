import os
import dash
import argparse

from werkzeug import Response
import authenticator
import config
from pages import editor, viewer, writer
from data_handler import init_database
from dash import html, dcc, Input, Output, State
import flask
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
from datetime import timedelta
import pyotp
from data_visualizer import umap_all_data

init_database()

# --- CONFIGURATION ---
server = flask.Flask(__name__)
server.config.update(
    SECRET_KEY=authenticator.get_server_secret_key(),
    REMEMBER_COOKIE_DURATION=timedelta(days=30)
)

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
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <link rel="manifest" href="/assets/manifest.json">
        <meta name="mobile-web-app-capable" content="yes">
        <meta name="theme-color" content="#2c3e50">
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''


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
            html.Div([
                html.H3("Writer"),
                html.P("Write a white paper based on ideas."),
                dcc.Link("Navigate", href="/writer", className="btn-secondary")
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
            dcc.Checklist(id='remember-me', options=[{'label': 'Remember me', 'value': 'remember'}], value=[]),
            html.Button('Connect', id='login-button', n_clicks=0, className="btn-primary"),
        ], className="form-stack"), 
        
        html.Div(id='login-error', className="error-msg")
    ], className="card login-card")
], className="page-wrapper center-content")


# Navigation bar, only visible if connected
def navbar() -> html.Nav:
    return html.Nav([
        dcc.Link('Home', href='/home', className="nav-link"),
        dcc.Link('Add ideas', href='/edit', className="nav-link"),
        dcc.Link('Vizualisation', href='/viz', className="nav-link"),
        dcc.Link('Writer', href='/writer', className="nav-link"),
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
    if pathname == '/writer': return writer.layout, nav
    return home_layout, nav 


@app.callback(
    [Output('url', 'pathname'), Output('login-error', 'children')],
    [Input('login-button', 'n_clicks')],
    [State('email', 'value'),
     State('pwd', 'value'),
     State('otp', 'value'),
     State('remember-me', 'remember')]
)
def auth_login(n_clicks, email: str, pwd: str, otp: str, remember_checked: bool):
    if n_clicks > 0:
        user_email, user_pwd = authenticator.get_user()
        if email == user_email and pwd == user_pwd:
            # Vérification du code Google Authenticator
            totp = pyotp.TOTP(authenticator.get_otp_secret())
            if totp.verify(otp) or config.DEBUG == True:
                remember = False
                if remember_checked:
                    remember = True
                print("auth successful")
                login_user(User(email), remember=remember)
                return '/', ''
            else:
                print("Code OTP invalide")
                return dash.no_update, "Code OTP invalide"
        return dash.no_update, "Identifiants incorrects"
    return dash.no_update, ""


@server.route('/logout')
def logout() -> Response:
    logout_user()
    return flask.redirect('/login')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Create user and generate Google Auth')
    parser.add_argument('-d', '--debug', help='generate a Google Auth for debug purpose', action="store_true")
    args = parser.parse_args()
    config.DEBUG = args.debug 
    app.run(debug=config.DEBUG)
