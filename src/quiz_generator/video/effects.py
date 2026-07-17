"""Efectos visuales avanzados y animados para el compositor de video.

Proporciona efectos estáticos (confeti, shake, glow, flash, viñeta,
zoom pulse) y efectos animados (partículas flotantes, countdown
circular, Ken Burns zoom, slide-in, text reveal, flash frames).

Los efectos animados generan secuencias de frames para crear
movimiento real a 60fps, eliminando la sensación estática.
"""

from __future__ import annotations

import math
import random
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont


class VisualEffects:
    """Colección de efectos visuales estáticos y animados.

    Los métodos estáticos aplican efectos sobre imágenes individuales.
    Los métodos de generación producen secuencias de frames para
    crear animaciones fluidas.
    """

    # =========================================================================
    # Efectos Estáticos (aplicar sobre una imagen)
    # =========================================================================

    @staticmethod
    def apply_confetti(
        img: Image.Image,
        num_particles: int = 80,
        particle_size: tuple[int, int] = (8, 20),
        seed: int | None = None,
    ) -> Image.Image:
        """Aplica un efecto de confeti sobre la imagen."""
        result = img.copy()
        draw = ImageDraw.Draw(result)
        rng = random.Random(seed)

        width, height = img.size

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

            particle = Image.new("RGBA", (w * 2, h * 2), (0, 0, 0, 0))
            p_draw = ImageDraw.Draw(particle)
            p_draw.rounded_rectangle(
                (w // 2, h // 2, w + w // 2, h + h // 2),
                radius=2,
                fill=(*color, alpha),
            )
            angle = rng.randint(0, 360)
            particle = particle.rotate(angle, expand=False, resample=Image.BICUBIC)

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
        """Aplica un efecto de vibración/shake."""
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
        """Aplica un efecto de brillo/glow."""
        glow_layer = Image.new("RGB", img.size, color)
        glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=radius))
        return Image.blend(img, glow_layer, intensity)

    @staticmethod
    def apply_zoom_pulse(
        img: Image.Image,
        factor: float = 1.05,
    ) -> Image.Image:
        """Aplica un efecto de zoom sutil (pulso de zoom)."""
        width, height = img.size
        new_w = int(width * factor)
        new_h = int(height * factor)

        zoomed = img.resize((new_w, new_h), Image.LANCZOS)

        left = (new_w - width) // 2
        top = (new_h - height) // 2
        return zoomed.crop((left, top, left + width, top + height))

    @staticmethod
    def apply_vignette(
        img: Image.Image,
        intensity: float = 0.6,
    ) -> Image.Image:
        """Aplica un efecto de viñeta oscura en los bordes.

        Versión optimizada usando numpy para velocidad.
        """
        width, height = img.size
        arr = np.array(img, dtype=np.float64)

        # Crear máscara radial con numpy (mucho más rápido)
        y_grid, x_grid = np.mgrid[0:height, 0:width]
        cx, cy = width / 2, height / 2
        max_radius = math.sqrt(cx ** 2 + cy ** 2)

        dist = np.sqrt((x_grid - cx) ** 2 + (y_grid - cy) ** 2)
        vignette = 1.0 - (dist / max_radius) ** 2 * intensity

        # Clamp
        vignette = np.clip(vignette, 0, 1)

        # Aplicar a cada canal
        for c in range(3):
            arr[:, :, c] *= vignette

        return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

    @staticmethod
    def apply_flash(
        img: Image.Image,
        color: tuple[int, int, int] = (255, 255, 255),
        intensity: float = 0.5,
    ) -> Image.Image:
        """Aplica un efecto de flash (destello)."""
        flash_layer = Image.new("RGB", img.size, color)
        return Image.blend(img, flash_layer, intensity)

    @staticmethod
    def apply_color_overlay(
        img: Image.Image,
        color: tuple[int, int, int],
        intensity: float = 0.2,
    ) -> Image.Image:
        """Aplica una capa de color semi-transparente."""
        overlay = Image.new("RGB", img.size, color)
        return Image.blend(img, overlay, intensity)

    @staticmethod
    def apply_drop_shadow_text(
        draw: ImageDraw.ImageDraw,
        text: str,
        x: int,
        y: int,
        font: ImageFont.FreeTypeFont,
        fill: tuple[int, int, int] = (255, 255, 255),
        shadow_color: tuple[int, int, int] = (0, 0, 0),
        shadow_offset: int = 3,
    ) -> None:
        """Dibuja texto con sombra para mayor legibilidad."""
        # Sombra
        draw.text((x + shadow_offset, y + shadow_offset), text,
                  fill=shadow_color, font=font)
        # Texto principal
        draw.text((x, y), text, fill=fill, font=font)

    @staticmethod
    def apply_text_outline(
        draw: ImageDraw.ImageDraw,
        text: str,
        x: int,
        y: int,
        font: ImageFont.FreeTypeFont,
        fill: tuple[int, int, int] = (255, 255, 255),
        outline_color: tuple[int, int, int] = (0, 0, 0),
        outline_width: int = 3,
    ) -> None:
        """Dibuja texto con outline grueso para máxima legibilidad."""
        for dx in range(-outline_width, outline_width + 1):
            for dy in range(-outline_width, outline_width + 1):
                if dx * dx + dy * dy <= outline_width * outline_width:
                    draw.text((x + dx, y + dy), text, font=font, fill=outline_color)
        draw.text((x, y), text, fill=fill, font=font)

    # =========================================================================
    # Efectos Animados Eager (Generan listas de imágenes)
    # NOTA: Mantener por compatibilidad, pero preferir las versiones "lazy" 
    #       para la composición de video.
    # =========================================================================

    @staticmethod
    def create_particles(
        width: int, 
        height: int, 
        num_particles: int = 30, 
        seed: int = 0,
    ) -> list[dict]:
        """Crea la definición matemática de las partículas flotantes.
        
        Útil para evaluación lazy (sin estado).
        """
        rng = random.Random(seed)
        colors = [
            (255, 215, 0, 120),    # Dorado
            (108, 92, 231, 100),   # Violeta
            (0, 206, 209, 110),    # Turquesa
            (255, 105, 180, 90),   # Rosa
            (0, 230, 118, 100),    # Verde
        ]

        particles = []
        for _ in range(num_particles):
            particles.append({
                "start_x": rng.uniform(0, width),
                "start_y": rng.uniform(0, height + 200),
                "size": rng.uniform(3, 8),
                "speed_y": rng.uniform(-40, -15),  # pixeles por segundo
                "speed_x": rng.uniform(-10, 10),
                "wobble_amp": rng.uniform(10, 40),
                "wobble_freq": rng.uniform(1, 3), # radianes por segundo
                "color": rng.choice(colors),
                "phase": rng.uniform(0, 2 * math.pi),
            })
        return particles

    @staticmethod
    def apply_particles_lazy(
        base_img: Image.Image,
        t: float,
        particles: list[dict],
    ) -> Image.Image:
        """Aplica partículas sobre un único frame en el instante t.
        
        Evaluación lazy matemática, no requiere estado previo.
        """
        width, height = base_img.size
        result = base_img.copy().convert("RGBA")
        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        for p in particles:
            # Calcular posición en el tiempo t
            raw_y = p["start_y"] + p["speed_y"] * t
            raw_x = p["start_x"] + p["speed_x"] * t + p["wobble_amp"] * math.sin(t * p["wobble_freq"] + p["phase"])
            
            # Wrap around (toroide)
            y = raw_y % (height + 40) - 20
            x = raw_x % (width + 40) - 20

            # Fade near top/bottom center (y = height/2 es opacidad máxima)
            alpha_ratio = 1 - abs(y / height - 0.5) * 0.8
            alpha = int(p["color"][3] * alpha_ratio)
            alpha = max(0, min(255, alpha))
            size = int(p["size"])

            draw.ellipse(
                (int(x) - size, int(y) - size,
                 int(x) + size, int(y) + size),
                fill=(*p["color"][:3], alpha),
            )

        result = Image.alpha_composite(result, overlay)
        return result.convert("RGB")

    @staticmethod
    def apply_ken_burns_lazy(
        img: Image.Image,
        t: float,
        duration: float,
        zoom_start: float = 1.0,
        zoom_end: float = 1.03,
    ) -> Image.Image:
        """Aplica Ken Burns zoom sobre un único frame en el instante t.
        
        Usa interpolación BILINEAR que es suficientemente rápida para
        ejecución real-time durante la composición de MoviePy.
        """
        # Calcular factor de zoom (ease-in-out)
        progress = max(0.0, min(1.0, t / max(duration, 0.001)))
        progress_eased = progress * progress * (3 - 2 * progress)
        factor = zoom_start + (zoom_end - zoom_start) * progress_eased

        width, height = img.size
        new_w = int(width * factor)
        new_h = int(height * factor)

        # Usar BILINEAR que es muy rápido (~10ms) en lugar de LANCZOS (~80ms)
        zoomed = img.resize((new_w, new_h), Image.BILINEAR)
        left = (new_w - width) // 2
        top = (new_h - height) // 2
        return zoomed.crop((left, top, left + width, top + height))

    @staticmethod
    def apply_flash_lazy(
        img: Image.Image,
        t: float,
        duration: float = 0.5,
        color: tuple[int, int, int] = (255, 255, 255),
        peak_intensity: float = 0.7,
    ) -> Image.Image:
        """Aplica un destello sobre un único frame en el instante t."""
        progress = max(0.0, min(1.0, t / duration))
        if progress >= 1.0:
            return img.copy()

        # Decaimiento exponencial (rápido al principio, lento al final)
        intensity = peak_intensity * math.exp(-4 * progress)
        flash_layer = Image.new("RGB", img.size, color)
        return Image.blend(img, flash_layer, max(0, min(1, intensity)))

    @staticmethod
    def generate_particle_frames(
        base_img: Image.Image,
        num_frames: int,
        num_particles: int = 30,
        seed: int = 0,
    ) -> list[Image.Image]:
        """Genera frames con partículas flotantes animadas.

        Las partículas flotan hacia arriba con movimiento ondulante,
        creando un efecto vivo y dinámico.

        Args:
            base_img: Imagen base sobre la que dibujar partículas.
            num_frames: Número de frames a generar.
            num_particles: Número de partículas.
            seed: Semilla aleatoria.

        Returns:
            Lista de imágenes con partículas animadas.
        """
        rng = random.Random(seed)
        width, height = base_img.size

        colors = [
            (255, 215, 0, 120),    # Dorado
            (108, 92, 231, 100),   # Violeta
            (0, 206, 209, 110),    # Turquesa
            (255, 105, 180, 90),   # Rosa
            (0, 230, 118, 100),    # Verde
        ]

        # Inicializar partículas
        particles = []
        for _ in range(num_particles):
            particles.append({
                "x": rng.uniform(0, width),
                "y": rng.uniform(0, height + 200),
                "size": rng.uniform(3, 8),
                "speed_y": rng.uniform(-1.5, -0.5),
                "speed_x": rng.uniform(-0.3, 0.3),
                "wobble_amp": rng.uniform(0.5, 2.0),
                "wobble_freq": rng.uniform(0.02, 0.05),
                "color": rng.choice(colors),
                "phase": rng.uniform(0, 2 * math.pi),
            })

        frames = []
        for frame_idx in range(num_frames):
            result = base_img.copy().convert("RGBA")
            overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)

            for p in particles:
                # Actualizar posición
                p["y"] += p["speed_y"]
                p["x"] += p["speed_x"] + p["wobble_amp"] * math.sin(
                    frame_idx * p["wobble_freq"] + p["phase"]
                )

                # Wrap around
                if p["y"] < -20:
                    p["y"] = height + 20
                    p["x"] = rng.uniform(0, width)
                if p["x"] < -20:
                    p["x"] = width + 20
                elif p["x"] > width + 20:
                    p["x"] = -20

                # Dibujar partícula con fade por posición
                alpha = int(p["color"][3] * (1 - abs(p["y"] / height - 0.5) * 0.5))
                alpha = max(0, min(255, alpha))
                size = int(p["size"])

                draw.ellipse(
                    (int(p["x"]) - size, int(p["y"]) - size,
                     int(p["x"]) + size, int(p["y"]) + size),
                    fill=(*p["color"][:3], alpha),
                )

            result = Image.alpha_composite(result, overlay)
            frames.append(result.convert("RGB"))

        return frames

    @staticmethod
    def generate_countdown_frames(
        base_img: Image.Image,
        timer_value: int,
        total_time: int,
        num_frames: int,
        center_x: int,
        center_y: int,
        radius: int = 45,
        font: ImageFont.FreeTypeFont | None = None,
        color_normal: tuple[int, int, int] = (108, 92, 231),
        color_warning: tuple[int, int, int] = (255, 214, 0),
        color_danger: tuple[int, int, int] = (255, 23, 68),
    ) -> list[Image.Image]:
        """Genera frames para un timer circular animado.

        El arco se reduce gradualmente y cambia de color según
        el tiempo restante.

        Args:
            base_img: Imagen base.
            timer_value: Valor actual del timer (segundos restantes).
            total_time: Tiempo total del timer.
            num_frames: Frames a generar para este segundo.
            center_x: X del centro del timer.
            center_y: Y del centro del timer.
            radius: Radio del círculo.
            font: Fuente para el número.
            color_normal: Color normal del arco.
            color_warning: Color de advertencia (≤5s).
            color_danger: Color de peligro (≤3s).

        Returns:
            Lista de frames con el timer animado.
        """
        # Seleccionar color
        if timer_value <= 3:
            color = color_danger
        elif timer_value <= 5:
            color = color_warning
        else:
            color = color_normal

        frames = []
        for f in range(num_frames):
            frame = base_img.copy()
            draw = ImageDraw.Draw(frame)

            # Calcular ángulo del arco (progreso dentro del segundo actual)
            progress_in_second = f / num_frames
            overall_progress = (timer_value - 1 + (1 - progress_in_second)) / total_time
            arc_angle = int(360 * overall_progress)

            # Dibujar fondo del arco (gris oscuro)
            draw.arc(
                (center_x - radius, center_y - radius,
                 center_x + radius, center_y + radius),
                0, 360,
                fill=(45, 45, 58),
                width=6,
            )

            # Dibujar arco de progreso
            if arc_angle > 0:
                draw.arc(
                    (center_x - radius, center_y - radius,
                     center_x + radius, center_y + radius),
                    -90, -90 + arc_angle,
                    fill=color,
                    width=6,
                )

            # Número del timer
            text = str(timer_value)
            if font:
                bbox = draw.textbbox((0, 0), text, font=font)
                text_w = bbox[2] - bbox[0]
                text_h = bbox[3] - bbox[1]

                # Pulsar el número en los últimos 3 segundos
                scale = 1.0
                if timer_value <= 3:
                    pulse = math.sin(progress_in_second * math.pi) * 0.15
                    scale = 1.0 + pulse

                draw.text(
                    (center_x - text_w // 2, center_y - text_h // 2 - 3),
                    text,
                    fill=color,
                    font=font,
                )

            frames.append(frame)

        return frames

    @staticmethod
    def apply_ken_burns(
        img: Image.Image,
        num_frames: int,
        zoom_start: float = 1.0,
        zoom_end: float = 1.03,
    ) -> list[Image.Image]:
        """Aplica efecto Ken Burns (zoom lento progresivo).

        Genera una secuencia de frames con zoom creciente,
        creando una sensación de movimiento sutil pero constante.

        Args:
            img: Imagen base.
            num_frames: Número de frames a generar.
            zoom_start: Factor de zoom inicial.
            zoom_end: Factor de zoom final.

        Returns:
            Lista de frames con zoom progresivo.
        """
        width, height = img.size
        frames = []

        for i in range(num_frames):
            t = i / max(num_frames - 1, 1)
            # Easing suave (ease-in-out)
            t_eased = t * t * (3 - 2 * t)
            factor = zoom_start + (zoom_end - zoom_start) * t_eased

            new_w = int(width * factor)
            new_h = int(height * factor)

            zoomed = img.resize((new_w, new_h), Image.LANCZOS)
            left = (new_w - width) // 2
            top = (new_h - height) // 2
            cropped = zoomed.crop((left, top, left + width, top + height))
            frames.append(cropped)

        return frames

    @staticmethod
    def generate_slide_in_frames(
        base_img: Image.Image,
        element_img: Image.Image,
        target_x: int,
        target_y: int,
        num_frames: int,
        direction: str = "right",
    ) -> list[Image.Image]:
        """Genera frames con un elemento que entra deslizándose.

        Args:
            base_img: Imagen de fondo.
            element_img: Elemento que se desliza.
            target_x: Posición X final.
            target_y: Posición Y final.
            num_frames: Número de frames de la animación.
            direction: Dirección de entrada ("right", "left", "bottom", "top").

        Returns:
            Lista de frames con la animación de slide-in.
        """
        width, height = base_img.size
        elem_w, elem_h = element_img.size

        # Calcular posición inicial fuera de pantalla
        if direction == "right":
            start_x, start_y = width + 50, target_y
        elif direction == "left":
            start_x, start_y = -elem_w - 50, target_y
        elif direction == "bottom":
            start_x, start_y = target_x, height + 50
        else:  # top
            start_x, start_y = target_x, -elem_h - 50

        frames = []
        for i in range(num_frames):
            t = i / max(num_frames - 1, 1)
            # Ease-out cubic
            t_eased = 1 - (1 - t) ** 3

            current_x = int(start_x + (target_x - start_x) * t_eased)
            current_y = int(start_y + (target_y - start_y) * t_eased)

            frame = base_img.copy()
            if element_img.mode == "RGBA":
                frame.paste(element_img, (current_x, current_y), element_img)
            else:
                frame.paste(element_img, (current_x, current_y))
            frames.append(frame)

        return frames

    @staticmethod
    def generate_flash_frames(
        img: Image.Image,
        num_frames: int = 6,
        color: tuple[int, int, int] = (255, 255, 255),
        peak_intensity: float = 0.7,
    ) -> list[Image.Image]:
        """Genera una secuencia de flash (blanco → normal).

        Args:
            img: Imagen final (después del flash).
            num_frames: Número de frames del flash.
            color: Color del flash.
            peak_intensity: Intensidad máxima del flash.

        Returns:
            Lista de frames con el flash decayendo.
        """
        frames = []
        flash_layer = Image.new("RGB", img.size, color)

        for i in range(num_frames):
            t = i / max(num_frames - 1, 1)
            # Decaimiento exponencial
            intensity = peak_intensity * math.exp(-3 * t)
            blended = Image.blend(img, flash_layer, max(0, min(1, intensity)))
            frames.append(blended)

        return frames

    @staticmethod
    def generate_text_reveal_opacity(
        num_words: int,
        total_frames: int,
        stagger: int = 3,
    ) -> list[list[float]]:
        """Calcula opacidades para revelar texto palabra por palabra.

        Args:
            num_words: Número de palabras a revelar.
            total_frames: Total de frames de la animación.
            stagger: Frames de delay entre cada palabra.

        Returns:
            Lista de listas: para cada frame, la opacidad de cada palabra [0..1].
        """
        fade_duration = max(4, total_frames // (num_words + 2))
        result = []

        for frame in range(total_frames):
            word_opacities = []
            for word_idx in range(num_words):
                start_frame = word_idx * stagger
                if frame < start_frame:
                    word_opacities.append(0.0)
                elif frame < start_frame + fade_duration:
                    progress = (frame - start_frame) / fade_duration
                    word_opacities.append(min(1.0, progress))
                else:
                    word_opacities.append(1.0)
            result.append(word_opacities)

        return result

    @staticmethod
    def draw_glowing_circle(
        draw: ImageDraw.ImageDraw,
        center: tuple[int, int],
        radius: int,
        color: tuple[int, int, int],
        glow_radius: int = 10,
    ) -> None:
        """Dibuja un círculo con efecto de brillo/glow."""
        cx, cy = center
        # Capas de glow (de mayor a menor, más transparentes)
        for i in range(glow_radius, 0, -2):
            alpha = int(30 * (1 - i / glow_radius))
            r = radius + i
            draw.ellipse(
                (cx - r, cy - r, cx + r, cy + r),
                fill=(*color, alpha) if draw._image.mode == "RGBA" else color,
                outline=None,
            )
        # Círculo principal
        draw.ellipse(
            (cx - radius, cy - radius, cx + radius, cy + radius),
            fill=color,
        )

    @staticmethod
    def draw_decorative_dots(
        draw: ImageDraw.ImageDraw,
        width: int,
        height: int,
        color: tuple[int, int, int] = (255, 255, 255),
        alpha: int = 20,
        num_dots: int = 50,
        seed: int = 42,
    ) -> None:
        """Dibuja puntos decorativos sutiles en el fondo."""
        rng = random.Random(seed)
        for _ in range(num_dots):
            x = rng.randint(0, width)
            y = rng.randint(0, height)
            size = rng.randint(1, 4)
            draw.ellipse(
                (x - size, y - size, x + size, y + size),
                fill=(*color, alpha) if hasattr(draw, "_image") and getattr(draw._image, "mode", "") == "RGBA" else color,
            )

    @staticmethod
    def draw_geometric_pattern(
        draw: ImageDraw.ImageDraw,
        width: int,
        height: int,
        color: tuple[int, int, int] = (255, 255, 255),
        opacity: float = 0.03,
        spacing: int = 60,
    ) -> None:
        """Dibuja un patrón geométrico sutil en el fondo (diamantes)."""
        line_color = tuple(int(c * opacity) for c in color)

        for x in range(0, width + spacing, spacing):
            for y in range(0, height + spacing, spacing):
                # Diamantes pequeños
                size = 8
                points = [
                    (x, y - size),
                    (x + size, y),
                    (x, y + size),
                    (x - size, y),
                ]
                draw.polygon(points, outline=line_color)
