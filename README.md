
# Ideas / Note handler
This application allows to enter new ideas or not and add tags to them. You can then visualize them in a smart way. 

# Install
To install the application, follow the steps: 
```
python3 -m venv venv
pip install -r requirements.txt
```

# Run
run the server in debug mode (local)
```
python app.py
```

# Generate user
To generate a single user with 2FA authenticator, execute the command line:
```
python authenticator.py <email> <password>
```
This will print a link that you can passed to Qr.io to generate a QR Code or directly paste in your Google Authenticator app.

## data storage
User account and ideas are stored in the directory called *data*. 

# Deployment in production
## Configure your router and Pi
- Open firewall and forward port 80 (http) & 443 (https) on your router
- Open your Raspberry Pi port 80 (http) & 443 (https)

## Install and run nginx
```
sudo apt install nginx
```

Configure nginx to serve your application
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

## Install and run Gunicorn on your system (prod server compared to debug dash server)
Gunicorn is a production server. Not like the own served by Dash. To go into production, use gunicorn.

Either once 
```
gunicorn --bind 0.0.0.0:8050 app:server
```
Or as a service started after each server restart.

```
sudo nano /etc/systemd/system/ideas_handler.service
```
With file content:
```
[Unit]
Description=Gunicorn instance to serve Ideas Handler
After=network.target

[Service]
User=[your user]
WorkingDirectory=/home/[your user]/ideas_topics
Environment="PATH=/home/[your user]/ideas_topics/venv/bin"
ExecStart=/home/[your user]/ideas_topics/venv/bin/gunicorn --workers 3 --bind 0.0.0.0:8050 app:server

[Install]
WantedBy=multi-user.target
```

Then restart the service
```
sudo systemctl daemon-reload
sudo systemctl restart ideas_handler.service
```

## Use a domain name instead of a public IP
Go to OVH and: 
- Buy a domain name (in our case pierreseroul.com)
- Configure the DNS: 
  - Go to Zone DNS
  - Select your domain
  - Change the 'A' type entries target by your public IP address. 

In your nginx configuration file, replace your **[your_public_ip_address]** by **[your_domain_name]**.

## Use certificates for https connection

