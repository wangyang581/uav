#-*- coding: UTF-8 -*-

import redis 
import numpy as np

class FaceDatabase:
    def __init__(self, redis_port, thres):
        redis_host = '127.0.0.1'
        self.r = redis.Redis(host=redis_host, port=redis_port, db=0)
        self.r2 = redis.Redis(host=redis_host, port=redis_port, db=1)
        self.thres = thres
        self.save_num = 10000
        
    def set(self, key, feature):
        feature = np.array(feature, dtype=np.float32)
        return self.r.set(key, feature.tobytes())

    def get(self, key):
        buffer = self.r.get(key)
        if buffer is None:
            return None 

        feature = np.frombuffer(buffer, dtype=np.float32)
        return feature 

    def delete(self, key):
        return self.r.delete(key)

    def keys(self):
        return [k.decode() for k in self.r.keys()]

    def top1(self, f, add_stranger):
        keys = []
        pipe = self.r.pipeline()

        for k in self.r.keys():
            keys.append(k.decode())
            pipe.get(k)

        features = pipe.execute()
        features = np.array([np.frombuffer(f, dtype=np.float32) for f in features])

        if len(keys):
            dist = np.dot(f, features.T)
            idx = np.argmax(dist)

            name = keys[idx]
            d = float(dist[idx])

            if d > self.thres:
                return (name, d)

        keys = []
        pipe = self.r2.pipeline()

        keys_arr = [int(key) for key in self.r2.keys()]
        max_num = max(keys_arr) if len(keys_arr) else 0

        del_key_arr = [] 
        for k in self.r2.keys():
            key = k.decode()
            keys.append(key)
            pipe.get(k)

            if max_num-self.save_num >= int(key):
                del_key_arr.append(key)

        features = pipe.execute()
        features = np.array([np.frombuffer(f, dtype=np.float32) for f in features])

        if len(keys):
            dist = np.dot(f, features.T)
            idx = np.argmax(dist)

            stranger_id = keys[idx]
            name = f'陌生人_{stranger_id}'
            d = float(dist[idx])

            if d > self.thres:
                return (name, d)
            
        if not add_stranger:
            return ('notfound', -2.0)

        f = np.array(f, dtype=np.float32)
        keys_arr = [int(key) for key in self.r2.keys()]
        max_num = max(keys_arr) if len(keys_arr) else 0

        stranger_id = max_num + 1
        name = f'陌生人_{stranger_id}'
        self.r2.set(stranger_id, f.tobytes())

        for del_key in del_key_arr:
            self.r2.delete(del_key) 

        return (name, 1.0) 
