import pyotp
import json
import argparse

def generate_auth_link(email: str, mdp: str, debug: bool) -> None:
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

def get_user() -> tuple[str, str]:
    with open("data/users.json", "r") as f:
        user = json.load(f)
    return user['email'], user['pwd']

def get_otp_secret(): 
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