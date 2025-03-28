import pygame
import constants
# Carregamento de imagens
def load_image(name, scale=None):
    try:
        img = pygame.image.load(name)
        if scale:
            img = pygame.transform.scale(img, scale)
        return img
    except:
        # Fallback caso a imagem não exista
        surf = pygame.Surface((50, 50), pygame.SRCALPHA)
        if "enemy" in name:
            pygame.draw.rect(surf, RED, (0, 0, 50, 50))
        elif "player" in name:
            pygame.draw.polygon(surf, constants.WHITE, [(25, 0), (0, 50), (50, 50)])
        return surf
