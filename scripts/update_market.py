from __future__ import annotations
import json, math, time
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import yfinance as yf

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/"data"/"market.json"
HISTORY_FILE=ROOT/"data"/"history.json"
CONFIG_FILE=ROOT/"config.json"

WATCHLIST=["SCHG","MSFT","AAPL","AMZN","GOOGL","META","NVDA","AVGO","TSM","ASML","V","MA","BRK-B","LLY","CEG","VRT","CRWD","PANW","COST","PLTR","AMD","MRVL","ANET","ETN","NOW","TSLA","RKLB","TEM","RXRX","IONQ","SNPS","CDNS","QUBT","AMAT","NFLX","ORCL","ISRG","MU","QCOM","RBLX","SNOW"]
BENCHMARKS=["SPY","QQQ","^VIX","IWM"]
SECTORS={"Technology":"XLK","Financials":"XLF","Healthcare":"XLV","Industrials":"XLI","Consumer Discretionary":"XLY","Energy":"XLE","Utilities":"XLU","Semiconductors":"SMH"}

def sf(v,d=0.0):
    try:
        n=float(v); return d if math.isnan(n) or math.isinf(n) else n
    except: return d

def rsi(s,p=14):
    d=s.diff(); g=d.clip(lower=0).rolling(p).mean(); l=(-d.clip(upper=0)).rolling(p).mean()
    return sf((100-(100/(1+g/l.replace(0,float("nan"))))).iloc[-1],50)

def series(data,t):
    try:return data["Close"][t] if isinstance(data.columns,pd.MultiIndex) else data["Close"]
    except:return pd.Series(dtype=float)

def analyze(t,s):
    s=s.dropna()
    if len(s)<55:return None
    price,prev=sf(s.iloc[-1]),sf(s.iloc[-2])
    sma20,sma50=sf(s.rolling(20).mean().iloc[-1]),sf(s.rolling(50).mean().iloc[-1])
    r=rsi(s); m=((price/sf(s.iloc[-21],price))-1)*100
    volatility=sf(s.pct_change().tail(20).std()*100)
    score=50; reasons=[]
    if price>sma20:score+=10;reasons.append("above 20-day trend")
    else:score-=10;reasons.append("below 20-day trend")
    if sma20>sma50:score+=12;reasons.append("positive intermediate trend")
    else:score-=12;reasons.append("weak intermediate trend")
    if 50<=r<=68:score+=10;reasons.append("healthy momentum")
    elif r>75:score-=9;reasons.append("overbought momentum")
    elif r<35:score-=6;reasons.append("weak momentum")
    if m>8:score+=8;reasons.append("strong one-month strength")
    elif m<-8:score-=8;reasons.append("negative one-month momentum")
    if volatility>4:score-=5;reasons.append("high volatility")
    score=int(max(0,min(100,round(score))))
    risk="High" if volatility>=4 else "Medium" if volatility>=2 else "Low"
    return {"ticker":"BRK.B" if t=="BRK-B" else t,"signal":"BUY" if score>=70 else "SELL" if score<43 else "HOLD","score":score,"price":round(price,2),"change_percent":round(((price/prev)-1)*100,2),"rsi":round(r,1),"risk":risk,"reason":", ".join(reasons[:4]).capitalize()+"."}

def get_news(config):
    results=[]; seen=set()
    for ticker in config.get("news_tickers",[])[:12]:
        try:
            for item in (yf.Ticker(ticker).news or [])[:4]:
                content=item.get("content",item)
                title=content.get("title") or item.get("title")
                link=(content.get("canonicalUrl") or {}).get("url") or item.get("link")
                if not title or not link or title in seen: continue
                seen.add(title)
                provider=content.get("provider") or {}
                results.append({"ticker":ticker,"title":title,"link":link,"publisher":provider.get("displayName") or item.get("publisher",""),"summary":content.get("summary","")[:280],"published":content.get("pubDate") or item.get("providerPublishTime",0)})
        except Exception as exc:
            print(f"News warning for {ticker}: {exc}")
        time.sleep(.15)
    results.sort(key=lambda x:str(x.get("published","")),reverse=True)
    return results[:config.get("max_news_items",12)]

def portfolio(config, items):
    prices={x["ticker"]:x["price"] for x in items}
    holdings=[]; total_value=total_cost=0.0
    for h in config.get("holdings",[]):
        ticker=h["ticker"]; shares=sf(h.get("shares")); cost=sf(h.get("cost_basis"))
        price=prices.get(ticker)
        if price is None:
            try: price=sf(yf.Ticker(ticker.replace(".","-")).fast_info["last_price"])
            except: price=0
        value=shares*price; gain=value-cost
        holdings.append({"ticker":ticker,"shares":shares,"cost_basis":round(cost,2),"price":round(price,2),"value":round(value,2),"gain":round(gain,2)})
        total_value+=value; total_cost+=cost
    return {"cash":sf(config.get("starting_cash",25)),"holdings":holdings,"total_value":round(total_value,2),"total_cost":round(total_cost,2),"total_gain":round(total_value-total_cost,2)}

def main():
    config=json.loads(CONFIG_FILE.read_text()) if CONFIG_FILE.exists() else {}
    all_tickers=WATCHLIST+BENCHMARKS+list(SECTORS.values())
    data=yf.download(all_tickers,period="9mo",interval="1d",auto_adjust=True,progress=False,threads=True)
    items=[x for t in WATCHLIST if (x:=analyze(t,series(data,t)))]
    items.sort(key=lambda x:x["score"],reverse=True)
    total=max(len(items),1); bp=round(sum(x["signal"]=="BUY" for x in items)/total*100); hp=round(sum(x["signal"]=="HOLD" for x in items)/total*100); sp=100-bp-hp
    score=round(sum(x["score"] for x in items)/total)
    label="Strong Buy" if score>=72 else "Cautiously Bullish" if score>=60 else "Neutral / Selective" if score>=48 else "Defensive"

    names={"SPY":"S&P 500","QQQ":"Nasdaq 100","^VIX":"VIX","IWM":"Russell 2000"}; metrics=[]
    for t in BENCHMARKS:
        s=series(data,t).dropna()
        if len(s)<2:continue
        p,q=sf(s.iloc[-1]),sf(s.iloc[-2]); ch=((p/q)-1)*100
        metrics.append({"label":names[t],"value":f"{p:.2f}" if t=="^VIX" else f"{p:.2f} ({ch:+.2f}%)","change_percent":round(-ch if t=="^VIX" else ch,2)})

    sectors=[]
    for name,ticker in SECTORS.items():
        s=series(data,ticker).dropna()
        if len(s)>=6:
            change=((sf(s.iloc[-1])/sf(s.iloc[-6]))-1)*100
            sectors.append({"name":name,"ticker":ticker,"change_percent":round(change,2)})
    sectors.sort(key=lambda x:x["change_percent"],reverse=True)

    top=[x for x in items if x["signal"]=="BUY"][:3] or items[:3]
    weights=[.5,.3,.2]; alloc=[{"ticker":x["ticker"],"amount":round(25*w,2),"reason":f"Score {x['score']} • {x['risk']} risk"} for x,w in zip(top,weights)]

    today=datetime.now(timezone.utc).date().isoformat()
    history=json.loads(HISTORY_FILE.read_text()) if HISTORY_FILE.exists() else []
    row={"date":today,"score":score,"buy_percent":bp,"hold_percent":hp,"sell_percent":sp,"leader":items[0]["ticker"] if items else ""}
    history=[h for h in history if h.get("date")!=today]+[row]
    history=history[-90:]
    HISTORY_FILE.write_text(json.dumps(history,indent=2))

    out={"generated_at":datetime.now(timezone.utc).isoformat(),"market_status":"Latest available close","market_temperature":{"label":label,"score":score,"buy_percent":bp,"hold_percent":hp,"sell_percent":sp},"market_metrics":metrics,"candidates":items[:30],"starter_allocation":alloc,"market_notes":[f"{bp}% of the watchlist qualifies as Buy.",f"Average score is {score}/100: {label}.",f"{items[0]['ticker']} leads with {items[0]['score']}/100." if items else "No candidates available."],"sectors":sectors,"news":get_news(config),"portfolio":portfolio(config,items),"history":history}
    OUTPUT.write_text(json.dumps(out,indent=2))

if __name__=="__main__":main()
