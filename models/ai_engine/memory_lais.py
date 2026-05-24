import time, json, hashlib
class DCTPMemory:
    def __init__(self):
        self.tiers={"T1":[],"T2":[],"T3":[],"T4":[]}; self.last=time.time()
    def add(self,t, tier="T2"):
        self.tiers[tier].append(t)
        if time.time()-self.last>1200: self.compress()
    def compress(self):
        self.tiers["T2"]=self.tiers["T2"][-20:]
        self.tiers["T3"]=[" ".join(x.split()[:8]) for x in self.tiers["T3"]]
        self.tiers["T4"]=self.tiers["T4"][-5:]; self.last=time.time()
    def state_hash(self): return hashlib.sha256(json.dumps(self.tiers).encode()).hexdigest()[:12]
