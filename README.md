# stor

Using a `Ubuntu 18.04 LTS` server on Google Cloud Platform:

## GCE server set up
```
sudo bash
apt-get update
apt-get install emacs25-nox
apt-get install virtualenv python-pip python-dev nginx

pushd /usr/bin/
rm python
ln -s python3 python

exit

cd
virtualenv -p /usr/bin/python3 venv
git clone https://github.com/DerwenAI/stor.git

cd stor
pip install -r requirements.txt
gsutil cp gs://computable-stor-config/* .
```


## Environment

Add these lines to your `~/.profile`:

```
source ~/venv/bin/activate
export GOOGLE_APPLICATION_CREDENTIALS="$HOME/test_api_key.json"
```


## Commands

Update config:
```
gsutil cp flask.cfg gs://computable-stor-config
```

Sync with Google Cloud Storage:
```
gsutil rsync -d -r static gs://computable-stor-config
```

For dev/test, use:
```
export FLASK_CONFIG="flask.cfg"
./app.py --builtin=5000
```

For testing in production env:
```
gunicorn --bind 0.0.0.0:5000 wsgi:app
```
