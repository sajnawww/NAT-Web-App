from flask import Flask, render_template, request, redirect
from nat_backend import NATTable
import socket
import subprocess
import time

app = Flask(__name__)
nat = NATTable()

logs = []
blocked_ips = set()

def log(msg):
    logs.append(f"[{time.strftime('%H:%M:%S')}] {msg}")

def get_ip():
    return socket.gethostbyname(socket.gethostname())

def get_host():
    return socket.gethostname()

def get_gateway():
    try:
        out = subprocess.check_output("ipconfig", shell=True).decode()
        return out.split("Default Gateway")[1].split("\n")[0].strip()
    except:
        return "Unavailable"

@app.route("/", methods=["GET", "POST"])
def index():
    search = request.args.get("search", "")

    if request.method == "POST":
        ip = request.form["ip"]
        port = int(request.form["port"])
        nat_type = request.form["type"]

        if ip in blocked_ips:
            log(f"Blocked attempt from {ip}")
            return redirect("/")

        if nat_type == "static":
            pub_ip, pub_port = nat.map_static(ip, port)
        else:
            pub_ip, pub_port = nat.map_dynamic(ip, port)

        log(f"{nat_type.upper()} → {ip}:{port} → {pub_ip}:{pub_port}")

        return redirect("/")

    filtered = {k: v for k, v in nat.nat_table.items() if search in k}

    return render_template(
        "index.html",
        table=filtered,
        logs=logs,
        ip=get_ip(),
        host=get_host(),
        gateway=get_gateway(),
        search=search
    )

@app.route("/simulate/<key>")
def simulate(key):
    priv = key
    pub = nat.nat_table[key]["public"]

    log(f"Packet flow: {priv} → NAT → {pub}")
    return redirect("/")

@app.route("/delete/<key>")
def delete(key):
    ip, port = key.split(":")
    nat.delete_mapping(ip, int(port))
    log(f"Deleted mapping {key}")
    return redirect("/")

@app.route("/clear")
def clear():
    nat.clear_table()
    log("Cleared NAT table")
    return redirect("/")

@app.route("/block", methods=["POST"])
def block():
    ip = request.form["block_ip"]
    blocked_ips.add(ip)
    log(f"Blocked IP: {ip}")
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)