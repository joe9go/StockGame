from http.server import BaseHTTPRequestHandler, HTTPServer
from http import HTTPStatus
from threading import Thread
import json
import yfinance as yf
import secrets
import time
import pickle
from blake3 import blake3

##TODO: Everything up here ought to be managed by a database. That's someone else's job, in my opinion.

with open("Data/company_list.json","r") as file:
    companies = json.load(file)['Stocks']
    
tickers = {}
for i in companies:
    tickers[i] = yf.Ticker(i)
    
with open("Data/predictions.dat","rb") as file:
    preds = pickle.load(file)
    predictions_date = preds['Date']
    predictions_user = preds['User']

with open("Data/scores.json","r") as file:
    user_scores = json.load(file)["Scores"]

#users are stored as username: salt, pass, token

with open("Data/users.json","r") as file:
    users = json.load(file)["Users"]

tokens = {}

##End of database TODO.

class Prediction:
    
    def __init__(self, company, date, value, user):
        self.company = company
        self.date = date
        self.value = value
        self.user = user
        self.start = time.time()

class Token:

    def __init__(self, user, expiry = 3600):
        self.value = secrets.randbits(128)
        self.start = time.time()
        self.user = user
        self.expiry = expiry

    def is_expired(self):
        return (time.time() - self.start - self.expiry) < 0

    def extend_token(self):
        if (time.time() - self.start - self.expiry) < (self.expiry/2):
            self.start = time.time()

    def get_user(self):
        if self.is_expired():
            return None
        extend_token()
        return user

class AuthError(Exception):
    pass
    
class RequestHandler(BaseHTTPRequestHandler):
    
    def _set_headers(self):
        self.send_response(HTTPStatus.OK.value)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin','*')
        self.end_headers()

    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "*")
        self.send_header("Access-Control-Allow-Headers", "*")

    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()
    
    def do_GET(self):
        length = int(self.headers.get('content-length'))
        print('GET')
        
    def do_POST(self):

        global a
        
        length = int(self.headers.get('content-length'))
        
        a = self.rfile.read(length)
        message = json.loads(a)
        try:
            msg = json.loads(message)
        except:
            msg = message
        print('POST', msg)
        
        post_type = self.headers.get('request')

        try:
            out = b''
            if post_type == "login":
                
                username = msg["username"]
                password = msg["password"]

                hashed = blake3(users[username][0].to_bytes(16,'big')+password.encode()).digest()
                if hashed == users[username][1].to_bytes(32,'big'):
                    token = Token(username)
                    tokens[token.value] = token
                    out = json.dumps({"token":token.value}).encode('utf-8')
                else:
                    raise AuthError

            elif post_type == "register":

                username = msg["username"]
                password = msg["password"]

                if username in users:
                    out = b'username taken'
                    
                else:
                    users[username][0] = secrets.randbits(128).to_bytes(16,'big')
                    users[username][1] = int.from_bytes(blake3(users[username][0]+password.encode()).digest(),'big')
                    
                    token = Token(username)
                    tokens[token.value] = token
                    out = json.dumps({"token":token.value}).encode('utf-8')
                
                
            elif post_type == "prediction":
                comp = msg["company"]
                date = msg["date"]
                value = msg["value"]
                user_token = msg["user_token"]
                user = tokens[user_token].get_user()

                if msg["user"] != user:
                    raise AuthError

                if user == None:
                    raise TimeoutError
                
                prediction = Prediction(comp,date,value,user)
                if date in predictions_date:
                    predictions_date[date].append(prediction)
                else:
                    predictions_date[date] = [prediction]
                if user in predictions_user:
                    predictions_user[user].append(prediction)
                else:
                    predictions_user[user] = [prediction]

                out = b'accepted prediction'
            
            elif post_type == 'history':
                
                comp = msg["company"]
                start = msg["start"]
                end = msg["end"]
                if comp in tickers:
                    hist = tickers[comp].history(start=start, end=end)
                    dates = [str(x) for x in hist.index.to_numpy()]
                    opens = list(hist["Open"].to_numpy())
                    
                    out = json.dumps({"dates":dates,"opens":opens}).encode('utf-8')
                    
            elif post_type == 'predictions':
                
##                user_token = msg["user_token"]
##                user = tokens[user_token].get_user()
##
##                if msg["user"] != user:
##                    raise AuthError

##                if user == None:
##                    raise TimeoutError

                user = msg["user"]
                
                predictions = predictions_user[user]
                dates = [x.date for x in predictions]
                values = [x.value for x in predictions]
                
                out = json.dumps({"dates":dates,"values":values}).encode('utf-8')
            
            else:
                raise ValueError
            
            self._set_headers()
            self.wfile.write(out)

        except TimeoutError:
            self.send_response(HTTPStatus.BAD_REQUEST.value)
            self.send_header('Access-Control-Allow-Origin','*')
            self.end_headers()
            self.wfile.write(b'client token expired')

            
        except AuthError:
            self.send_response(HTTPStatus.BAD_REQUEST.value)
            self.send_header('Access-Control-Allow-Origin','*')
            self.end_headers()
            self.wfile.write(b'client token invalid')
            
        except Exception:
            self.send_response(HTTPStatus.BAD_REQUEST.value)
            self.send_header('Access-Control-Allow-Origin','*')
            self.end_headers()
            self.wfile.write(b'')
        
port = 9876
server = HTTPServer(('', port), RequestHandler)

def runServer():

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass

    server.server_close()

def clear_tokens():
    
    for i in list(tokens.keys()):
        if tokens[i].is_expired:
            tokens.pop(i)
        

def collect_scores():
    for p in prediction_date[time.strftime("%Y-%m-%d")]:
        start = yfinance.history(p.company)
        hist = list(p.company.history(start=p.start, end=p.start)["Open"]).to_numpy[0]
        now = list(p.company.history(start=p.end, end=p.end)["Open"]).to_numpy[0]
        user_scores[p.user] += ((p.value-hist)/hist-(now-hist)/hist)/((now-hist)/hist)

def autosave():
    while True:
        time.sleep(1800)
            
        with open("Data/predictions.dat","wb") as file:
            pickle.dump({"Date":predictions_date,"User":{}},predictions_user)
        
        with open("Data/scores.json","w+") as file:
            data = {"Scores":user_scores}
            json.dump(data,file)
        
        with open("Data/users.json","w+") as file:
            data = {"Users":users}
            json.dump(data,file)

tokenMan = Thread(target = clear_tokens, daemon=True)
saveMan = Thread(target = autosave, daemon=True)

tokenMan.start()
saveMan.start()

runServer()
autosave()
