from http.server import BaseHTTPRequestHandler, HTTPServer
from http import HTTPStatus
from threading import Thread
import json
import yfinance as yf
import secrets
import time
from datetime import datetime, timedelta
import pickle
from blake3 import blake3

class Prediction:
    
    def __init__(self, company, date, value, user):
        self.company = company
        self.date = date
        self.value = value
        self.user = user
        self.start = time.strftime("%Y-%m-%d")

class Token:

    def __init__(self, user, expiry = 3600):
        self.value = secrets.randbits(128)
        self.start = time.time()
        self.user = user
        self.expiry = expiry

    def is_expired(self):
        return (time.time() - self.start) > self.expiry

    def extend_token(self):
        if (time.time() - self.start - self.expiry) > (self.expiry/2):
            self.start = time.time()

    def get_user(self):
        if self.is_expired():
            return None
        self.extend_token()
        return self.user

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
        
        length = int(self.headers.get('content-length'))
        a = self.rfile.read(length)
        print(a)
        message = json.loads(a)
        try:
            msg = json.loads(message)
        except:
            msg = message
        
        post_type = self.headers.get('request')

        if(post_type != "login" and post_type != "register"):
            print('POST', msg)

        try:
            out = b''
            if post_type == "login":

                username = msg["username"]
                password = msg["password"]

                print("User With Username:",username,"Attempted Login")

                hashed = blake3(users[username][0].to_bytes(16,'big')+password.encode()).digest()
                if hashed == users[username][1].to_bytes(32,'big'):
                    token = Token(username)
                    tokens[token.value] = token
                    out = json.dumps({"token":str(token.value)}).encode('utf-8')
                else:
                    raise AuthError

            elif post_type == "register":

                username = msg["username"]
                password = msg["password"]

                print("New User Registered With Username:",username)

                if username in users:
                    out = b'username taken'
                    
                else:
                    users[username] = [None, None]
                    users[username][0] = int(secrets.randbits(128))
                    users[username][1] = int.from_bytes(blake3(users[username][0].to_bytes(16,'big')+password.encode()).digest(),'big')
                    
                    token = Token(username)
                    tokens[token.value] = token
                    out = json.dumps({"token":str(token.value)}).encode('utf-8')
                
                
            elif post_type == "prediction":
                comp = msg["company"]
                date = msg["date"]
                value = int(msg["value"])
                user_token = int(msg["user_token"])
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

                user = msg["user"]
                
                predictions = predictions_user[user]
                dates = [x.date for x in predictions]
                values = [x.value for x in predictions]
                
                out = json.dumps({"dates":dates,"values":values}).encode('utf-8')

            elif post_type == 'leaderboard':
                
                board = []
                for username in users:
                    if username in user_scores:
                        score = user_scores[username]/len(predictions_user[username])
                        board.append((username, score))
                    
                board.sort(key=lambda x: x[1])
                
                out = json.dumps({"scores":board[0:10]}).encode('utf-8')
            
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
    if time.strftime("%Y-%m-%d") in predictions_date:
        curTime = time.strftime("%Y-%m-%d")
        for p in predictions_date[curTime]:
            ticker = tickers(p.company)
            start_value = ticker.history(start=0, end=date_incr(p.start))["Open"].to_numpy()[0]
            now_value = ticker.history(start=curTime, end=date_incr(curTime))["Open"].to_numpy()[0]
            
            pctOff = (p.value-start_value)/start_value-(now_value-start_value)/start_value

            score = (-10*abs(pctOff)**0.5 + 100)/(25*pctOff**2+1)
            
            if p.user in user_scores:
                user_scores[p.user] += score

            user_scores[p.user] = score

def date_incr(date):
    return (datetime.strptime(date, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')

def arti_collect_scores(date, start=None):
    if date in predictions_date:
        curTime = date
        for p in predictions_date[curTime]:
            ticker = tickers[p.company]
            
            start_value = ticker.history(start=0, end=date_incr(p.start))["Open"].to_numpy()[0]
            
            now_value = ticker.history(start=curTime, end=date_incr(curTime))["Open"].to_numpy()[0]
            
            pctOff = (p.value-start_value)/start_value-(now_value-start_value)/start_value

            score = (-10*abs(pctOff)**0.5 + 100)/(25*pctOff**2+1)

            if p.user in user_scores:
                user_scores[p.user] += score

            user_scores[p.user] = score

def autosave():
    while True:
        time.sleep(300)
        print("saving")
            
        with open("Data/predictions.dat","wb") as file:
            pickle.dump({"Date":predictions_date,"User":predictions_user},file)
        
        with open("Data/scores.json","w+") as file:
            data = {"Scores":user_scores}
            json.dump(data,file)
        
        with open("Data/users.json","w+") as file:
            data = {"Users":users}
            json.dump(data,file)
        print("saved")

def keepscore():
    while True:
        time.sleep(3600*24)
        collect_scores()


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

tokenMan = Thread(target = clear_tokens, daemon=True)
saveMan = Thread(target = autosave, daemon=True)
scoreMan = Thread(target = keepscore, daemon=True)
servMan = Thread(target = runServer)

tokenMan.start()
saveMan.start()
scoreMan.start()
servMan.start()
