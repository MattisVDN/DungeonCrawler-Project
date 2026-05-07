# -*- coding: utf-8 -*-
import random
from settings import *

class Camera:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.shake_timer = 0
        self.shake_intensity = 0

    def trigger_shake(self, frames, intensity):
        self.shake_timer = frames
        self.shake_intensity = intensity

    def update(self, target):
        # 1. Bereken de standaard positie (gecentreerd op de speler)
        self.x = target.x - (WIDTH // 2) + (target.width // 2)
        self.y = target.y - (HEIGHT // 2) + (target.height // 2)

        # 2. Voeg de trilling toe als de timer aan staat!
        if self.shake_timer > 0:
            self.x += random.randint(-self.shake_intensity, self.shake_intensity)
            self.y += random.randint(-self.shake_intensity, self.shake_intensity)
            self.shake_timer -= 1