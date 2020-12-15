from flask import Flask, request
import config
import hashlib
import json

app = Flask(__name__)

@app.route('/api', methods=['GET', 'POST'])
def api():
  #?value=&appid=&secret=
  value = request.args.get('value')
  appid = request.args.get('appid')
  secret = request.args.get('secret')
  if value is None or appid is None or secret is None:
    return config.errors[0] # missing some data in url
  else:
    if secret == config.APItoken.getSecret(str(appid)):
      return config.cureword.cureparse(
        str(value),
        str(request.method),
        json.loads(request.get_data(as_text=True)),
        str(appid)
        )
    else:
      return config.errors[1] #sign verify failed

@app.route('/')
def main():
  return config.errors[4]

if __name__ == '__main__':
    app.run(host='127.0.0.1',port=8443)