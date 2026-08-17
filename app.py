from flask import Flask, render_template, request, jsonify
import csv, os

app = Flask(__name__)
FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "members.csv")
FIELDS = ["ID","Name","Address","Phone","EntryFees","JoinDate","MembershipType","Gender"]

def load():
    if not os.path.exists(FILE): return []
    out=[]
    with open(FILE, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            try:
                r["ID"]=int(r["ID"]); r["EntryFees"]=float(r["EntryFees"])
                out.append(r)
            except: pass
    return out

def save(rows):
    with open(FILE,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=FIELDS); w.writeheader(); w.writerows(rows)

@app.get("/")
def home(): return render_template("index.html")

@app.get("/api/members")
def members(): return jsonify(load())

@app.get("/api/summary")
def summary():
    rows=load(); total=len(rows); revenue=sum(r["EntryFees"] for r in rows)
    return jsonify({
        "total":total,"revenue":revenue,
        "average":revenue/total if total else 0,
        "male":sum(r["Gender"].lower()=="male" for r in rows),
        "female":sum(r["Gender"].lower()=="female" for r in rows),
        "types": {t:sum(r["MembershipType"]==t for r in rows) for t in set(r["MembershipType"] for r in rows)}
    })

@app.post("/api/members")
def add():
    d=request.get_json(); rows=load()
    try: fee=float(d["EntryFees"])
    except: return jsonify(error="Invalid fee"),400
    m={"ID":max([r["ID"] for r in rows],default=0)+1,
       "Name":d["Name"].strip().upper(),"Address":d["Address"].strip(),
       "Phone":d["Phone"].strip(),"EntryFees":fee,"JoinDate":d["JoinDate"],
       "MembershipType":d["MembershipType"].title(),"Gender":d["Gender"].title()}
    rows.append(m); save(rows); return jsonify(m),201

@app.put("/api/members/<int:i>")
def update(i):
    d=request.get_json(); rows=load()
    for r in rows:
        if r["ID"]==i:
            for k in ["Name","Address","Phone","JoinDate"]:
                if str(d.get(k,"")).strip(): r[k]=str(d[k]).strip()
            if d.get("Name"): r["Name"]=r["Name"].upper()
            if d.get("MembershipType"): r["MembershipType"]=d["MembershipType"].title()
            if d.get("Gender"): r["Gender"]=d["Gender"].title()
            if str(d.get("EntryFees","")).strip():
                try:r["EntryFees"]=float(d["EntryFees"])
                except:return jsonify(error="Invalid fee"),400
            save(rows); return jsonify(r)
    return jsonify(error="Member not found"),404

@app.delete("/api/members/<int:i>")
def delete(i):
    rows=load(); new=[r for r in rows if r["ID"]!=i]
    if len(new)==len(rows): return jsonify(error="Member not found"),404
    save(new); return jsonify(ok=True)

if __name__=="__main__":
    app.run(debug=True)