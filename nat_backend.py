import json
import random
import time
import os

class NATTable:
    def __init__(self, file="nat_table.json"):
        self.file = file
        self.nat_table = {}
        self.reverse_table = {}
        self._load()

    def _load(self):
        if os.path.exists(self.file):
            try:
                with open(self.file, "r") as f:
                    self.nat_table = json.load(f)
            except:
                self.nat_table = {}
        else:
            self._save()
        self._rebuild()

    def _save(self):
        with open(self.file, "w") as f:
            json.dump(self.nat_table, f, indent=4)

    def _rebuild(self):
        self.reverse_table = {}
        for priv, entry in self.nat_table.items():
            self.reverse_table[entry["public"]] = priv

    def generate_public_ip(self):
        return f"203.0.113.{random.randint(1,254)}"

    def map_dynamic(self, private_ip, private_port):
        key = f"{private_ip}:{private_port}"

        if key in self.nat_table:
            pub_ip, pub_port = self.nat_table[key]["public"].split(":")
            return pub_ip, int(pub_port)

        public_ip = self.generate_public_ip()

        used_ports = [
            int(v["public"].split(":")[1])
            for v in self.nat_table.values()
            if v["public"].startswith(public_ip)
        ]

        while True:
            port = random.randint(30000, 60000)
            if port not in used_ports:
                break

        self.nat_table[key] = {
            "public": f"{public_ip}:{port}",
            "timestamp": int(time.time())
        }

        self._rebuild()
        self._save()

        return public_ip, port

    def map_static(self, private_ip, private_port):
        key = f"{private_ip}:{private_port}"

        public_ip = self.generate_public_ip()

        self.nat_table[key] = {
            "public": f"{public_ip}:{private_port}",
            "timestamp": int(time.time())
        }

        self._rebuild()
        self._save()

        return public_ip, private_port

    def delete_mapping(self, ip, port):
        key = f"{ip}:{port}"
        if key in self.nat_table:
            del self.nat_table[key]
            self._save()
            return True
        return False

    def clear_table(self):
        self.nat_table = {}
        self.reverse_table = {}
        self._save()