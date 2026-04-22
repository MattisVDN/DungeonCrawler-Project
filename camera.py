# -*- coding: utf-8 -*-
"""
Created on Mon Mar 16 16:07:37 2026

@author: VDNSpare
"""
# camera.py
from settings import *

class Camera:
    def __init__(self):
        self.x = 0
        self.y = 0

    def update(self, target):
        self.x = target.x - (WIDTH // 2) + (target.width // 2)
        self.y = target.y - (HEIGHT // 2) + (target.height // 2)