"""Efectos visuales avanzados para el compositor de video.

Proporciona efectos como confeti, shake, glow, flash, viñeta
y zoom pulse que se aplican sobre imágenes Pillow para
enriquecer las escenas del quiz.
"""

from __future__ import annotations

import math
import random
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont


class VisualEffects:
    """Colección de efectos visuales estáticos aplicables a imágenes Pillow.

    Cada efecto recibe una imagen y devuelve una nueva imagen con el
    efecto aplicado, sin modificar la original.
    """

    @staticmethod
    def apply_confetti(
        img: Image.Image,
        num_particles: int = 80,
        particle_size: tuple[int, int] = (8, 20),
        seed: int | None = None,
    ) -> Image.Image:
        """Aplica un efecto de confeti sobre la imagen.

        Genera partículas coloridas rectangulares rotadas aleatoriamente
        que simulan confeti cayendo. Ideal para revelar respuesta correcta.

        Args:
            img: Imagen base.
            num_particles: Cantidad de partículas de confeti.
            particle_size: Rango (min, max) de tamaño de cada partícula.
            seed: Semilla aleatoria para reproducibilidad.

        Returns:
            Nueva imagen con confeti superpuesto.
        """
        result = img.copy()
        draw = ImageDraw.Draw(result)
        rng = random.Random(seed)

        width, height = img.size

        # Colores vibrantes para confeti
        confetti_colors = [
            (255, 215, 0),    # Dorado
            (255, 69, 0),     # Rojo-naranja
            (0, 206, 209),    # Turquesa
            (255, 105, 180),  # Rosa
            (50, 205, 50),    # Verde lima
            (255, 165, 0),    # Naranja
            (138, 43, 226),   # Violeta
            (0, 191, 255),    # Azul cielo
            (255, 255, 0),    # Amarillo
        ]

        for _ in range(num_particles):
            x = rng.randint(0, width)
            y = rng.randint(0, height)
            w = rng.randint(particle_size[0], particle_size[1])
            h = rng.randint(particle_size[0] // 2, particle_size[1] // 2)
            color = rng.choice(confetti_colors)
            alpha = rng.randint(180, 255)

            # Crear partícula rotada como overlay
            particle = Image.new("RGBA", (w * 2, h * 2), (0, 0, 0, 0))
            p_draw = ImageDraw.Draw(particle)
            p_draw.rounded_rectangle(
                (w // 2, h // 2, w + w // 2, h + h // 2),
                radius=2,
                fill=(*color, alpha),
            )
            angle = rng.randint(0, 360)
            particle = particle.rotate(angle, expand=False, resample=Image.BICUBIC)

            # Pegar partícula
            result.paste(
                particle.convert("RGB"),
                (x - w, y - h),
                particle.split()[3] if particle.mode == "RGBA" else None,
            )

        return result

    @staticmethod
    def apply_shake(
        img: Image.Image,
        intensity: int = 5,
        seed: int | None = None,
    ) -> Image.Image:
        """Aplica un efecto de vibración/shake desplazando la imagen.

        Útil para revelar respuestas incorrectas o momentos de tensión.

        Args:
            img: Imagen base.
            intensity: Magnitud máxima del desplazamiento en píxeles.
            seed: Semilla aleatoria para reproducibilidad.

        Returns:
            Nueva imagen desplazada aleatoriamente.
        """
        rng = random.Random(seed)
        dx = rng.randint(-intensity, intensity)
        dy = rng.randint(-intensity, intensity)

        width, height = img.size
        result = Image.new("RGB", (width, height), (0, 0, 0))
        result.paste(img, (dx, dy))
        return result

    @staticmethod
    def apply_glow(
        img: Image.Image,
        color: tuple[int, int, int] = (108, 92, 231),
        radius: int = 20,
        intensity: float = 0.4,
    ) -> Image.Image:
        """Aplica un efecto de brillo/glow alrededor de los bordes brillantes.

        Ideal para resaltar la respuesta correcta con un aura luminosa.

        Args:
            img: Imagen base.
            color: Color RGB del glow.
            radius: Radio del desenfoque.
            intensity: Intensidad del glow (0.0 a 1.0).

        Returns:
            Nueva imagen con efecto glow.
        """
        # Crear overlay del color
        glow_layer = Image.new("RGB", img.size, color)
        glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=radius))

        # Mezclar con la imagen original
        result = Image.blend(img, glow_layer, intensity)
        return result

    @staticmethod
    def apply_zoom_pulse(
        img: Image.Image,
        factor: float = 1.05,
    ) -> Image.Image:
        """Aplica un efecto de zoom sutil (pulso de zoom).

        Escala la imagen ligeramente y recorta al tamaño original.
        Ideal para transiciones o momentos de énfasis.

        Args:
            img: Imagen base.
            factor: Factor de zoom (1.05 = 5% más grande).

        Returns:
            Nueva imagen con zoom aplicado.
        """
        width, height = img.size
        new_w = int(width * factor)
        new_h = int(height * factor)

        # Escalar
        zoomed = img.resize((new_w, new_h), Image.LANCZOS)

        # Recortar al tamaño original (centrado)
        left = (new_w - width) // 2
        top = (new_h - height) // 2
        result = zoomed.crop((left, top, left + width, top + height))

        return result

    @staticmethod
    def apply_vignette(
        img: Image.Image,
        intensity: float = 0.6,
    ) -> Image.Image:
        """Aplica un efecto de viñeta oscura en los bordes.

        Oscurece los bordes de la imagen para dar un efecto cinematográfico
        que dirige la atención al centro.

        Args:
            img: Imagen base.
            intensity: Intensidad del oscurecimiento (0.0 a 1.0).

        Returns:
            Nueva imagen con viñeta.
        """
        width, height = img.size
        result = img.copy()

        # Crear máscara de viñeta con gradiente radial
        vignette = Image.new("L", (width, height), 0)
        draw = ImageDraw.Draw(vignette)

        cx, cy = width // 2, height // 2
        max_radius = math.sqrt(cx ** 2 + cy ** 2)

        for y in range(height):
            for x in range(0, width, 4):  # Saltar píxeles para velocidad
                dist = math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
                ratio = min(dist / max_radius, 1.0)
                darkness = int(ratio * ratio * intensity * 255)
                draw.rectangle((x, y, x + 4, y + 1), fill=darkness)

        # Invertir: centro claro, bordes oscuros
        vignette_inv = Image.new("L", (width, height), 255)
        vignette_inv = Image.composite(
            Image.new("L", (width, height), 0),
            vignette_inv,
            vignette,
        )

        # Aplicar como máscara de luminosidad
        dark = Image.new("RGB", (width, height), (0, 0, 0))
        result = Image.composite(dark, result, vignette_inv)

        return result

    @staticmethod
    def apply_flash(
        img: Image.Image,
        color: tuple[int, int, int] = (255, 255, 255),
        intensity: float = 0.5,
    ) -> Image.Image:
        """Aplica un efecto de flash (destello blanco o de color).

        Ideal para el momento de revelar la respuesta.

        Args:
            img: Imagen base.
            color: Color RGB del flash.
            intensity: Intensidad del flash (0.0 = sin flash, 1.0 = completamente blanco).

        Returns:
            Nueva imagen con flash aplicado.
        """
        flash_layer = Image.new("RGB", img.size, color)
        return Image.blend(img, flash_layer, intensity)

    @staticmethod
    def apply_color_overlay(
        img: Image.Image,
        color: tuple[int, int, int],
        intensity: float = 0.2,
    ) -> Image.Image:
        """Aplica una capa de color semi-transparente.

        Útil para dar tono verde (correcto) o rojo (incorrecto).

        Args:
            img: Imagen base.
            color: Color RGB del overlay.
            intensity: Intensidad del overlay (0.0 a 1.0).

        Returns:
            Nueva imagen con overlay de color.
        """
        overlay = Image.new("RGB", img.size, color)
        return Image.blend(img, overlay, intensity)
