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
        # Bereken waar de camera EIGENLIJK moet zijn (gecentreerd op speler)
        target_x = target.x - (WIDTH // 2) + (target.width // 2)
        target_y = target.y - (HEIGHT // 2) + (target.height // 2)

        # LERP: Beweeg de camera elke frame vloeiend met 10% richting het doel
        self.x += (target_x - self.x) * 0.1
        self.y += (target_y - self.y) * 0.1

        # Trilling toevoegen
        if self.shake_timer > 0:
            self.x += random.randint(-self.shake_intensity, self.shake_intensity)
            self.y += random.randint(-self.shake_intensity, self.shake_intensity)
            self.shake_timer -= 1