# -*- coding: utf-8 -*-

WIDTH = 800
HEIGHT = 600
FPS = 60
TILE_SIZE = 43

# Kleuren
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
GOLD = (255, 215, 0)
GREEN = (0, 255, 0)
GRASS_GREEN = (34, 139, 34)
TREE_GREEN = (0, 100, 0)
CASTLE_GRAY = (50, 50, 50)
DUNGEON_GRAY = (100, 100, 100)


def check_botsing(rect1, rect2):
    """
    Controleert of twee rechthoeken overlappen via AABB wiskunde.
    Vervangt pygame.Rect.colliderect() 
    """
    return (rect1.x < rect2.x + rect2.width and
            rect1.x + rect1.width > rect2.x and
            rect1.y < rect2.y + rect2.height and
            rect1.y + rect1.height > rect2.y)

def check_punt_botsing(x, y, rect):
    """
    Controleert of een exact (x, y) punt in een rechthoek valt.
    Vervangt pygame.Rect.collidepoint().
    """
    return (rect.x <= x <= rect.x + rect.width and
            rect.y <= y <= rect.y + rect.height)