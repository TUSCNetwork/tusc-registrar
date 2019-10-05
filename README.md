# tusc-registrar

This program handles registering new accounts on the TUSC network. The intention is for it to run behind an nginx 
server and handle api security before forwarding account registration requests to a TUSC cli wallet running on the same
machine. This allows limiting account registration requests from the same IP within x hours via the 
`general:ip_request_blocking_hours` config value as well as requiring a valid Captcha response in the request.

Built with Python 3.7.3

Setting up an AWS node:

AMI: amzn2-ami-hvm-2.0.20190618-x86_64-gp2 (ami-0d8f6eb4f641ef691)

1. Get prereqs:
    1. `sudo yum update -y`
    1. `sudo yum install git gcc python3 python3-dev postgresql postgresql-server postgresql-libs postgresql-devel docker python3-devel`
    1. `sudo pip3 install web3 requests flask pyyaml psycopg2 pyopenssl flask-cors wheel gunicorn`
    1. `sudo amazon-linux-extras install nginx1.12`
1. Setup wallet:
    1. `sudo service docker start`
    1. `sudo docker run -it -P {wallet image}`
    1. In the wallet cli
        1. Ctrl-p, ctrl-q (to detach from the docker image)
    1. `sudo docker container ls`
        1. Find the CONTAINER ID of the running docker image
    1. `sudo docker commit {container id} swap-wallet`
    1. `sudo docker attach {container id}`
    1. In the wallet cli
        1. `quit`
    1. `sudo docker run -it -p 5071:8091 -e param="-H 0.0.0.0:8091" swap-wallet`
    1. In the wallet cli
        1. `set_password {password}`
        1. `unlock {password}`
        1. `suggest_brain_key`
        1. `create_account_with_brain_key "brain... key" occtotusc nathan nathan true`
        1. `transfer nathan occtotusc 10000 TUSC "Your 1st TUSC!" true`
        1. `upgrade_account occtotusc true`
        1. `save_wallet_file my-wallet.json`
        1. Ctrl-p, ctrl-q (to detach from the docker image)
    1. `sudo docker commit {container id} swap-wallet`
1. Setup db:
    1. `sudo postgresql-setup initdb`
    1. `sudo systemctl enable postgresql.service`
    1. `sudo service postgresql start`
    1. `sudo -u postgres psql`
    1. You'll be in the PSQL prompt now.
    1. Change the postgres user password
        1. `ALTER USER postgres WITH PASSWORD '{password}';`
    1. Make the tusc-registrar database and tables:
        1. `create database "tusc-registrar";`
        1. `\q`
    1. `sudo nano /var/lib/pgsql/data/pg_hba.conf`
        1. Change the local domain socket connection and the IPv4 connection from "peer" to "md5" and save it
    1. `sudo service postgresql restart`
    1. Connect to the new db
        1. `psql "tusc-registrar" postgres`
        1. Run the two `create table` commands in db_access/scripts/0001-init.sql
        1. `\q`
1. Setup code:
    1. `mkdir registrar`
    1. `cd registrar`
    1. `git clone https://github.com/TUSCNetwork/tusc-registrar.git`
    1. `sudo chown -R ec2-user ~/registrar/tusc-registrar`
    1. `cd tusc-registrar`
    1. `sudo python3 -m venv env`
    1. `sudo chown -R ec2-user env/`
1. Set the local_config.yaml settings:
    1. cd `~/registrar/tusc-registrar/configs`
    1. `sudo nano local_config.yaml`
    1. Ensure the `db:password`, `db:user`, `tusc_api:registrar_account_name`, `general:captcha_secret` are all set correctly.
1. Setup service:
    1. `source env/bin/activate`
    1. `pip install web3 requests flask pyyaml psycopg2 pyopenssl flask-cors gunicorn`
    1. `deactivate`
    1. `sudo cp tusc-registrar.service /etc/systemd/system/tusc-registrar.service`
    1. `sudo systemctl start tusc-registrar`
    1. `sudo systemctl enable tusc-registrar`
1. Setup server:
    1. `sudo nano /etc/nginx/nginx.conf`
        1. Look in notes for nginx config
    1. `sudo systemctl enable nginx`
    1. `sudo systemctl start nginx`
1. Run the registrar (for dev)
    1. `screen -S registrar`
    1. `cd ~/registrar/tusc-registrar/`
    1. `sudo python3 registrar_main.py`
    1. Ctrl-a, Ctrl-d (to detach from the screen running registrar)
1. Run the registrar (for prod, without service)
    1. `source env/bin/activate`
    1. `gunicorn --bind 0.0.0.0:8080 registrar_wsgi:app`
    1. Ctrl-a, Ctrl-d (to detach from the screen running registrar)
