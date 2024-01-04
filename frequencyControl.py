import time
from .cacheout import LRUCache


class HeatBar:
    def __init__(self, inertia=30, moment=3, cool=0) -> None:
        self.step = inertia
        self.limit = inertia * (moment-1)
        self.cool = cool
        self.time = LRUCache(maxsize=512, ttl=300, default=0)
        self.release = LRUCache(maxsize=64, ttl=300, default=0)
        self.release_number = []

    def setattr(self,name:str=None,value:int=0):     
        if name == 'inertia':
            self.step = (round(value, 2))
        if name == 'moment':
            self.limit = self.step * round(value-1, 2)
        if name == 'cool':
            self.cool = value

    def __respond(self,key:int):
        exceed = self.time.get(key) - time.time()

        if self.limit > 0 and exceed > self.limit:
            self.time.set(key, 0)
            release_time = time.time() + self.cool + exceed - self.limit
            self.release.set(key, release_time) 
            self.release_number.append(key)

    def check(self, key:int) -> int:
        ban = self.release.get(key) - time.time()
        return int(ban) if ban > 0 else 0
    
    def trigger(self, key:int, step:int=0) -> int:
        step = step or self.step
        if ban := self.check(key):
            return ban
        
        else:
            if (t := self.time.get(key)) > time.time():
                self.time.set(key, t + step) 
            else: 
                self.time.set(key, time.time() + step)

            self.__respond(key)

            return 0

