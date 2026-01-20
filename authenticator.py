import pyotp
import json
import argparse

def generate_auth_link(email: str, mdp: str, debug: bool) -> None:
    """
    Generate authentication link and save user credentials.
    
    Creates a Google Authenticator secret and saves user credentials to a JSON file.
    Generates a provisioning URI for QR code generation.
    
    Args:
        email (str): User's email address
        mdp (str): User's password
        debug (bool): Whether to enable debug mode
        
    Returns:
        None
    """
    otp_secret = pyotp.random_base32()
    
    user = {
    "email": email,
    "pwd": mdp,
    "otp_secret": otp_secret}

    json_str = json.dumps(user, indent=4)
    with open("data/users.json", "w") as f:
        f.write(json_str)

    totp = pyotp.TOTP(otp_secret)
    appname = 'IdeaManager'
    if debug: 
        appname = "IdeaManagerDebug"

    print(f"Pasted the following link in Qr.io to obtain a QR code : {totp.provisioning_uri(name=appname, issuer_name='ServerPi')}")

def get_server_secret_key() -> str:
    """
    Retrieve the server's secret key from configuration.
    
    Reads the secret key from the server configuration file.
    
    Returns:
        str: The server's secret key
    """
    with open("data/server.json", "r") as f:
        user = json.load(f)
    return user['secret_key']

def get_user() -> tuple[str, str]:
    """
    Retrieve user credentials from configuration.
    
    Reads user email and password from the user configuration file.
    
    Returns:
        tuple[str, str]: A tuple containing (email, password)
    """
    with open("data/users.json", "r") as f:
        user = json.load(f)
    return user['email'], user['pwd']

def get_otp_secret(): 
    """
    Retrieve the user's Google Authenticator secret.
    
    Reads the OTP secret from the user configuration file.
    
    Returns:
        str: The user's Google Authenticator secret
    """
    with open("data/users.json", "r") as f:
        user = json.load(f)
    return user['otp_secret']

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Create user and generate Google Auth')
    parser.add_argument('email', type=str, help='Email of the user')
    parser.add_argument('pwd', type=str, help='Password of the user')
    parser.add_argument('-d', '--debug', help='generate a Google Auth for debug purpose', action="store_true")

    args = parser.parse_args()

    generate_auth_link(args.email, args.pwd, args.debug)
