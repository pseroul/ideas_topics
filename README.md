
# Ideas / Note handler
This application allows to enter new **ideas/descriptions** or **title/notes** and add **tags** to them. You can then visualize them in a smart way. 

# Install
To install the application, follow the steps: 
```
python3 -m venv venv
pip install -r requirements.txt
```

# Run
### Generate user
To generate a single user with 2FA authenticator, execute the command line:
```
python authenticator.py <email> <password> (--debug)
```
This will print a link that you can passed to Qr.io to generate a QR Code or directly paste in your Google Authenticator app.
You can use the optional *--debug* argument To create a debug Auth. It helps if you want to have one auth for your production environment and another one for debug purpose.

### Generate server secret key
Create a file called ```data/server.json``` and fill it with this model (change the secret_key):`
```
{
    "secret_key" : "my_very_secret_server_key"
}
```


### Run the server in debug mode (local)
```
python app.py
```

### data storage
User account and ideas are stored in the directory called *data*. 


# Deployment in production
## Configure your router and Pi
- Open firewall and forward port 80 (http) & 443 (https) on your router (look at your router documentation)
- Open your Raspberry Pi port 80 (http) & 443 (https):
```
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw reload
```


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

### Either run it once:
```
gunicorn --bind 0.0.0.0:8050 app:server
```
### Or as a service started after each server restart:

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
- Buy a domain name
- Configure the DNS: 
  - Go to Zone DNS
  - Select your domain
  - Change the 'A' type entries target by your public IP address. 

In your nginx configuration file, replace your **[your_public_ip_address]** by **[your_domain_name]**.

## Use certificates for https connection
> Warning: this is only feasible if you have a domain name and not a public IP address.

Install and run Certbot:
```
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d [your_domain.com]
```
Skip email address settings...

Certbot rewrite your nginx configuration with the appropriate certificates.

Close http port:
```
sudo ufw delete allow 80/tcp
sudo ufw reload
```