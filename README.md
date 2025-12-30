
# Ideas / Note handler
This application allows to enter new ideas or not and add tags to them. You can then visualize them in a smart way. 

## Install
To install the application, follow the steps: 
```
python3 -m venv venv
pip install -r requirements.txt
```

## Run
### run the server in debug mode (local)
```
python app.py
```

### run the server in production mode
- Open firewall and forward port 80 (http) & 443 (https) on your router
- Install and nginx on your system
```
sudo apt install nginx
```
- Install and run Gunicorn on your system
```
gunicorn --bind 0.0.0.0:8050 app:server
```
- Configure nginx to serve your application
  - Create file */etc/nginx/sites-available/ideas_handler* and paste the following code:
```
gserver {
    listen 80;
    server_name [your_public_ip_address];

    location / {
        proxy_pass http://127.0.0.1:8050;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```
  - Add symbolic link to unabled site
  ```
  sudo ln -s /etc/nginx/sites-available/ideas_handler /etc/nginx/sites-enabled/
  ```
  - Restart nginx
  ```
  sudo systemctl restart nginx
  ```

#### Use a domain name instead of a public IP
Go to OVH and: 
- Buy a domain name (in our case pierreseroul.com)
- Configure the DNS: 
  - Go to Zone DNS
  - Select your domain
  - Change the 'A' type entries target by your public IP address. 

#### Use certificates for https connection

## Generate user
To generate a single user with 2FA authenticator, execute the command line:
```
python authenticator.py <email> <password>
```
This will print a link that you can passed to Qr.io to generate a QR Code or directly paste in your Google Authenticator app.

## data storage
User account and ideas are stored in the directory called *data*. 