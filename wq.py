import requests
import pandas as pd
import numpy as np


# Create a session to persistently store the headers
s = requests.Session()

# Save credentials into session
s.auth = (username, password)

# Send a POST request to the /authentication API
response = s.post('https://api.worldquantbrain.com/authentication')
response.status_code


def Simulation(alpha):
    simulate_data = {
        "type": "REGULAR",
        "settings": {
            "instrumentType": "EQUITY",
            "region": "USA",
            "universe": "TOP3000",
            "delay": 1,
            "decay": 15,
            "neutralization": "SUBINDUSTRY",
            "truncation": 0.08,
            "pasteurization": "ON",
            "unitHandling": "VERIFY",
            "nanHandling": "OFF",
            "language": "FASTEXPR",
            "visualization": False,
        },
        "regular": alpha
    }
    simulate_response = s.post('https://api.worldquantbrain.com/simulations', json=simulate_data)

    simulation_progress_url = simulate_response.headers['Location']
    finished = False
    while True:
        simulation_progress = s.get(simulation_progress_url)
        if simulation_progress.headers.get("Retry-After", 0) == 0:
            break
        # print("Sleeping for " + simulation_progress.headers["Retry-After"] + " seconds")

        import time
        time.sleep(float(simulation_progress.headers["Retry-After"]))
    # print("Alpha done simulating, getting alpha details")
    alpha = simulation_progress.json()["alpha"]
    simulation_result = s.get("https://api.worldquantbrain.com/alphas/" + alpha)

    pnl = s.get("https://api.worldquantbrain.com/alphas/" + alpha)  
    return pnl.json()

a = pd.read_csv("fields.csv")

fields = a.values.reshape(1,-1).tolist()[0]
import math

kq = [i for i in range(len(a)-1)]
next_index = len(a)-1
for i in range(next_index,len(fields)-1):
    kq.append(Simulation("group_rank(rank({}/{}),sector)".format(fields[i],fields[i+1])))
    if i == 0:
        pd.DataFrame([kq[i]]).to_csv("alpha.csv",mode="a",header=True)
    else:
        pd.DataFrame([kq[i]]).to_csv("alpha.csv",mode="a",header=False)

# convert best alpha
results = pd.read_csv('alpha.csv')
results = results.loc[:,['id','is']]

#check fitness and sharp
b = results['is'].tolist()

def change_to_float(a):
    while not a[-1].isnumeric():
        a = a[:len(a)-1]
        change_to_float(a)
    return a

for i in range(len(b)):
    fitness = float(change_to_float(b[i][b[i].index('fitness')+9:b[i].index('fitness')+15]))
    sharpe = float(change_to_float(b[i][b[i].index('sharpe')+9:b[i].index('sharpe')+15]))
    if abs(fitness) >= 1 and abs(sharpe) >= 1.25:
        results.iloc[i].to_csv("passall.csv",mode = "a",header = False)
    elif abs(fitness) >=1 or abs(sharpe) >= 1.25:
        results.iloc[i].to_csv("only1.csv",mode = "a",header = False)

# function

def mae3bound(alpha):
    return f"le1 = sum(close,20)/20 - sum(close,20)/20 * 0.05; le2 = sum(close,20)/20 - sum(close,20)/20 * 0.1;le3 = sum(close,20)/20 - sum(close,20)/20 * 0.2; alpha = {alpha};low < le3?alpha + 0.5781*abs(alpha):(low<le2?alpha+0.2254*abs(alpha):(low<le1?alpha+0.078*abs(alpha):alpha))"
kq = Simulation(mae3bound("group_rank(rank({}/{}),sector)".format("close","open")))
def MACD(alpha):
    return f"WMA12=decay_linear(close,12);WMA26=decay_linear(close,26);MACDLine =  WMA12 - WMA26;SignalLine=decay_linear(MACDLine,9);MACDHistogram = MACDLine - SignalLine; alpha = {alpha};MACDHistogram > 0? alpha + 0.11234*abs(alpha):alpha"
def Bollinger_Bands(alpha):
    return f"MB=sum(close,20)/20;UB=MB+2*stddev(close,20);LB=MB-2*stddev(close,20);alpha = {alpha};low<LB ? alpha + 0.1531*abs(alpha):alpha"
def RSI(alpha):
    return f"AG=sum((delta(close,1) > 0 ? delta(close,1) : 0), 14);AL=sum((delta(close,1)< 0 ? - delta(close,1) : 0), 14);RSI = (100 - 100 / (1 +  AG/AL)); alpha = {alpha}; RSI < 30? alpha + 0.2451*abs(alpha): alpha"
def ROC(alpha):
