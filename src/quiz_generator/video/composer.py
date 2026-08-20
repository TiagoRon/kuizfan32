"""Compositor de escenas premium — genera fotogramas con Pillow.

Crea las imágenes/fotogramas de cada escena del quiz usando
Pillow para renderizar texto, fondos, opciones, temporizadores,
barras de progreso y otros elementos visuales.

Diseño premium con:
- Fondos gradiente multi-punto con patrón geométrico
- Texto con sombra y outline para legibilidad
- Cards glassmorphism para opciones de respuesta
- Labels en círculos de color
- Barra de progreso con gradiente y glow
- Timer circular animado
- Soporte completo de emojis via FontManager
- Decoraciones visuales (puntos, líneas, iconos)
"""

from __future__ import annotations

import logging
import math
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from quiz_generator.config import Settings
from quiz_generator.video.font_manager import FontManager

logger = logging.getLogger(__name__)


class SceneComposer:
    """Compositor de escenas visuales premium usando Pillow.

    Genera imágenes de alta calidad para cada fotograma del video,
    con diseño moderno, tipografía profesional, y soporte de emojis.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._width = settings.video.ancho
        self._height = settings.video.alto
        self._colors = settings.video.colores
        self._fonts_config = settings.video.fuentes
        self._font_manager = FontManager(
            cache_dir=settings.assets.directorio_fuentes,
        )
        self._last_timer_y = 400  # Updated dynamically by render_question_scene

    def _get_font(self, family: str, size: int) -> ImageFont.FreeTypeFont:
        """Obtiene una fuente via FontManager con caché."""
        return self._font_manager.get_font(family, size)

    def _get_emoji_font(self, size: int) -> ImageFont.FreeTypeFont | None:
        """Obtiene la fuente de emojis."""
        return self._font_manager.get_emoji_font(size)

    def _hex_to_rgb(self, hex_color: str) -> tuple[int, int, int]:
        """Convierte color hexadecimal a tupla RGB."""
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))  # type: ignore[return-value]

    def _hex_to_rgba(self, hex_color: str, alpha: int = 255) -> tuple[int, int, int, int]:
        """Convierte color hexadecimal a tupla RGBA."""
        r, g, b = self._hex_to_rgb(hex_color)
        return (r, g, b, alpha)

    # =========================================================================
    # Sistema de Temas de Fondo — 6 variantes que rotan por pregunta
    # =========================================================================

    _BACKGROUND_THEMES = [
        {  # 0: Nebula Cosmos — nubes cósmicas + estrellas
            "gradient_top": (12, 10, 30),
            "gradient_mid": (30, 15, 60),
            "gradient_bottom": (8, 20, 40),
            "nebula_colors": [
                (108, 92, 231, 14), (0, 206, 209, 12),
                (255, 105, 180, 10), (80, 60, 200, 12),
            ],
            "orb_colors": [
                (108, 92, 231), (0, 206, 209), (255, 105, 180),
                (160, 120, 255), (0, 200, 150),
            ],
            "accent": (108, 92, 231),
            "style": "nebula",
        },
        {  # 1: Ocean Deep — ondas fluidas azul/verde + burbujas
            "gradient_top": (5, 15, 35),
            "gradient_mid": (0, 40, 70),
            "gradient_bottom": (0, 60, 80),
            "nebula_colors": [
                (0, 120, 180, 14), (0, 200, 170, 12),
                (0, 80, 140, 10), (30, 180, 220, 11),
            ],
            "orb_colors": [
                (0, 180, 220), (0, 220, 180), (30, 140, 200),
                (0, 250, 200), (80, 200, 255),
            ],
            "accent": (0, 180, 220),
            "style": "ocean",
        },
        {  # 2: Neon Inferno — rayas diagonales neon + partículas
            "gradient_top": (25, 5, 15),
            "gradient_mid": (50, 10, 30),
            "gradient_bottom": (20, 5, 25),
            "nebula_colors": [
                (255, 50, 100, 14), (255, 140, 0, 12),
                (255, 200, 0, 10), (200, 0, 80, 11),
            ],
            "orb_colors": [
                (255, 50, 100), (255, 140, 0), (255, 200, 50),
                (200, 0, 120), (255, 80, 80),
            ],
            "accent": (255, 50, 100),
            "style": "neon",
        },
        {  # 3: Crystal Grid — red hexagonal + reflejos cristalinos
            "gradient_top": (10, 10, 25),
            "gradient_mid": (15, 20, 45),
            "gradient_bottom": (5, 10, 30),
            "nebula_colors": [
                (100, 140, 255, 12), (180, 200, 255, 10),
                (60, 100, 200, 11), (140, 160, 240, 9),
            ],
            "orb_colors": [
                (120, 160, 255), (180, 200, 255), (80, 120, 220),
                (200, 220, 255), (100, 180, 255),
            ],
            "accent": (120, 160, 255),
            "style": "crystal",
        },
        {  # 4: Aurora Borealis — bandas curvadas luminosas
            "gradient_top": (5, 10, 20),
            "gradient_mid": (10, 25, 35),
            "gradient_bottom": (5, 15, 25),
            "nebula_colors": [
                (0, 255, 130, 14), (0, 200, 255, 12),
                (100, 255, 200, 10), (0, 180, 160, 11),
            ],
            "orb_colors": [
                (0, 255, 130), (0, 200, 255), (100, 255, 200),
                (50, 220, 180), (0, 180, 255),
            ],
            "accent": (0, 255, 130),
            "style": "aurora",
        },
        {  # 5: Electric Storm — rayos estilizados + chispas
            "gradient_top": (15, 5, 25),
            "gradient_mid": (25, 10, 50),
            "gradient_bottom": (10, 5, 30),
            "nebula_colors": [
                (180, 0, 255, 14), (255, 255, 0, 10),
                (0, 200, 255, 12), (200, 100, 255, 11),
            ],
            "orb_colors": [
                (180, 0, 255), (255, 220, 0), (0, 200, 255),
                (200, 100, 255), (255, 150, 255),
            ],
            "accent": (180, 0, 255),
            "style": "electric",
        },
    ]

    def _create_gradient_background(
        self,
        color_top: str | None = None,
        color_bottom: str | None = None,
        add_pattern: bool = True,
        theme_index: int = 0,
    ) -> Image.Image:
        """Crea un fondo premium con degradado vertical, patrón temático y variación por pregunta."""
        img = Image.new("RGBA", (self._width, self._height))
        draw = ImageDraw.Draw(img)

        theme = self._BACKGROUND_THEMES[theme_index % len(self._BACKGROUND_THEMES)]

        if color_top and color_bottom:
            top = self._hex_to_rgb(color_top)
            mid = tuple((a + b) // 2 for a, b in zip(top, self._hex_to_rgb(color_bottom)))
            bottom = self._hex_to_rgb(color_bottom)
        else:
            top = theme["gradient_top"]
            mid = theme["gradient_mid"]
            bottom = theme["gradient_bottom"]

        # Gradiente tri-punto (top → mid → bottom) para más riqueza
        half_h = self._height // 2
        for y in range(self._height):
            if y < half_h:
                ratio = y / half_h
                ratio = ratio * ratio * (3 - 2 * ratio)
                r = int(top[0] + (mid[0] - top[0]) * ratio)
                g = int(top[1] + (mid[1] - top[1]) * ratio)
                b = int(top[2] + (mid[2] - top[2]) * ratio)
            else:
                ratio = (y - half_h) / half_h
                ratio = ratio * ratio * (3 - 2 * ratio)
                r = int(mid[0] + (bottom[0] - mid[0]) * ratio)
                g = int(mid[1] + (bottom[1] - mid[1]) * ratio)
                b = int(mid[2] + (bottom[2] - mid[2]) * ratio)
            draw.line([(0, y), (self._width, y)], fill=(r, g, b, 255))

        # Patrón temático
        if add_pattern:
            self._draw_themed_pattern(draw, theme, seed=theme_index * 100 + 42)

        return img

    def _draw_themed_pattern(
        self,
        draw: ImageDraw.ImageDraw,
        theme: dict,
        seed: int = 42,
    ) -> None:
        """Dibuja un patrón de fondo basado en el tema seleccionado.

        Cada tema tiene su propio estilo visual único:
        - nebula: nubes cósmicas + estrellas + orbs conectados
        - ocean: ondas fluidas + burbujas + reflejos
        - neon: rayas diagonales neon + partículas de fuego
        - crystal: red hexagonal + reflejos cristalinos
        - aurora: bandas curvadas luminosas + cielo estrellado
        - electric: rayos estilizados + chispas + red eléctrica
        """
        import random
        rng = random.Random(seed)
        w, h = self._width, self._height
        style = theme.get("style", "nebula")
        nebula_colors = theme["nebula_colors"]
        orb_colors = theme["orb_colors"]
        accent = theme["accent"]

        # === Paso 1: Nubes difusas / nebulas (todos los temas) ===
        num_clouds = 8 if style in ("nebula", "aurora") else 6
        max_cloud_r = 220 if style in ("nebula", "aurora") else 160
        for _ in range(num_clouds):
            nx = rng.randint(-150, w + 150)
            ny = rng.randint(-150, h + 150)
            nc = rng.choice(nebula_colors)
            for radius in range(max_cloud_r, 0, -7):
                alpha = int(nc[3] * (1 - radius / max_cloud_r) ** 0.5)
                if alpha > 0:
                    draw.ellipse(
                        (nx - radius, ny - radius, nx + radius, ny + radius),
                        fill=(nc[0], nc[1], nc[2], alpha),
                    )

        # === Paso 2: Patrón geométrico específico del tema ===
        if style == "nebula":
            # Grid diagonal cruzado tenue
            line_color = (255, 255, 255, 6)
            spacing = 90
            for x in range(-h, w + h, spacing):
                draw.line([(x, 0), (x - h // 2, h)], fill=line_color, width=1)
                draw.line([(x, 0), (x + h // 2, h)], fill=line_color, width=1)

        elif style == "ocean":
            # Ondas sinusoidales horizontales
            for wave_i in range(12):
                wave_y = rng.randint(0, h)
                wave_alpha = rng.randint(6, 15)
                points = []
                for px in range(0, w + 20, 8):
                    dy = int(30 * math.sin(px / 120 + wave_i * 0.7))
                    points.append((px, wave_y + dy))
                if len(points) >= 2:
                    draw.line(points, fill=(*accent, wave_alpha), width=2)
            # Burbujas
            for _ in range(40):
                bx = rng.randint(0, w)
                by = rng.randint(0, h)
                br = rng.randint(3, 12)
                ba = rng.randint(8, 25)
                draw.ellipse(
                    (bx - br, by - br, bx + br, by + br),
                    outline=(*accent, ba), width=1,
                )
                # Reflejo de luz en burbuja
                rr = max(1, br // 3)
                draw.ellipse(
                    (bx - br + 2, by - br + 2, bx - br + 2 + rr, by - br + 2 + rr),
                    fill=(255, 255, 255, ba),
                )

        elif style == "neon":
            # Rayas diagonales neon con brillo
            for stripe_i in range(18):
                sx = rng.randint(-h, w + h)
                stripe_alpha = rng.randint(8, 20)
                stripe_color = rng.choice(orb_colors)
                stripe_w = rng.randint(1, 3)
                draw.line(
                    [(sx, 0), (sx - h // 3, h)],
                    fill=(*stripe_color, stripe_alpha), width=stripe_w,
                )
            # Chispas de fuego (puntos brillantes)
            for _ in range(60):
                sx = rng.randint(0, w)
                sy = rng.randint(0, h)
                ss = rng.randint(1, 4)
                sa = rng.randint(30, 90)
                sc = rng.choice(orb_colors)
                draw.ellipse(
                    (sx - ss, sy - ss, sx + ss, sy + ss),
                    fill=(*sc, sa),
                )

        elif style == "crystal":
            # Red hexagonal
            hex_size = 80
            hex_alpha = 8
            for row in range(-2, h // hex_size + 3):
                for col in range(-2, w // hex_size + 3):
                    cx = int(col * hex_size * 1.5)
                    cy = int(row * hex_size * math.sqrt(3) + (col % 2) * hex_size * math.sqrt(3) / 2)
                    # Dibujar hexágono
                    hex_points = []
                    for vi in range(6):
                        angle = math.radians(60 * vi + 30)
                        hx = cx + int(hex_size * 0.5 * math.cos(angle))
                        hy = cy + int(hex_size * 0.5 * math.sin(angle))
                        hex_points.append((hx, hy))
                    if len(hex_points) == 6:
                        draw.polygon(hex_points, outline=(*accent, hex_alpha))
            # Reflejos cristalinos (líneas brillantes cortas)
            for _ in range(25):
                lx = rng.randint(0, w)
                ly = rng.randint(0, h)
                ll = rng.randint(15, 50)
                la = rng.randint(10, 25)
                angle = rng.uniform(0, math.pi)
                x2 = lx + int(ll * math.cos(angle))
                y2 = ly + int(ll * math.sin(angle))
                draw.line([(lx, ly), (x2, y2)], fill=(255, 255, 255, la), width=1)

        elif style == "aurora":
            # Bandas curvadas luminosas
            for band_i in range(6):
                band_y = rng.randint(h // 6, h * 5 // 6)
                band_color = rng.choice(orb_colors)
                band_alpha_base = rng.randint(6, 14)
                band_thickness = rng.randint(40, 100)
                for dy in range(-band_thickness, band_thickness, 3):
                    alpha = int(band_alpha_base * (1 - abs(dy) / band_thickness) ** 2)
                    if alpha <= 0:
                        continue
                    points = []
                    for px in range(0, w + 20, 12):
                        curve_y = band_y + dy + int(
                            50 * math.sin(px / 200 + band_i * 1.5)
                            + 25 * math.sin(px / 80 + band_i * 3)
                        )
                        points.append((px, curve_y))
                    if len(points) >= 2:
                        draw.line(points, fill=(*band_color, alpha), width=1)

        elif style == "electric":
            # Rayos estilizados
            for _ in range(5):
                sx = rng.randint(w // 4, w * 3 // 4)
                sy = rng.randint(0, h // 4)
                bolt_color = rng.choice(orb_colors)
                bolt_alpha = rng.randint(12, 25)
                points = [(sx, sy)]
                for _ in range(rng.randint(6, 12)):
                    last = points[-1]
                    nx = last[0] + rng.randint(-60, 60)
                    ny = last[1] + rng.randint(40, 120)
                    points.append((nx, ny))
                    if ny > h:
                        break
                if len(points) >= 2:
                    draw.line(points, fill=(*bolt_color, bolt_alpha), width=2)
                    # Glow del rayo
                    draw.line(points, fill=(*bolt_color, bolt_alpha // 3), width=6)
            # Red eléctrica (líneas finas conectando puntos)
            nodes = [(rng.randint(0, w), rng.randint(0, h)) for _ in range(15)]
            for i, (x1, y1) in enumerate(nodes):
                for x2, y2 in nodes[i + 1:]:
                    dist = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
                    if dist < 400:
                        la = int(6 * (1 - dist / 400))
                        if la > 0:
                            draw.line([(x1, y1), (x2, y2)], fill=(*accent, la), width=1)

        # === Paso 3: Orbs de luz (todos los temas) ===
        orbs = []
        num_orbs = 12 if style in ("nebula", "crystal") else 8
        for _ in range(num_orbs):
            ox = rng.randint(30, w - 30)
            oy = rng.randint(30, h - 30)
            orb_color = rng.choice(orb_colors)
            orb_size = rng.randint(30, 80)
            orbs.append((ox, oy, orb_color, orb_size))

            # Halo exterior difuso
            for radius in range(orb_size + 35, orb_size, -3):
                alpha = int(5 * (1 - (radius - orb_size) / 35))
                draw.ellipse(
                    (ox - radius, oy - radius, ox + radius, oy + radius),
                    fill=(*orb_color, alpha),
                )
            # Orb principal con glow
            for radius in range(orb_size, 0, -4):
                alpha = int(12 * (1 - radius / orb_size) ** 0.7)
                draw.ellipse(
                    (ox - radius, oy - radius, ox + radius, oy + radius),
                    fill=(*orb_color, alpha),
                )
            # Núcleo brillante
            core_r = max(3, orb_size // 5)
            draw.ellipse(
                (ox - core_r, oy - core_r, ox + core_r, oy + core_r),
                fill=(*orb_color, 40),
            )

        # === Paso 4: Líneas de energía entre orbs cercanos ===
        for i, (x1, y1, c1, _) in enumerate(orbs):
            for x2, y2, _, _ in orbs[i + 1:]:
                dist = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
                if dist < 500:
                    line_alpha = int(10 * (1 - dist / 500))
                    if line_alpha > 0:
                        draw.line(
                            [(x1, y1), (x2, y2)],
                            fill=(*c1, line_alpha),
                            width=1,
                        )

        # === Paso 5: Estrellas con twinkle (todos los temas) ===
        num_stars = 120 if style in ("nebula", "aurora", "electric") else 80
        for _ in range(num_stars):
            x = rng.randint(0, w)
            y = rng.randint(0, h)
            size = rng.randint(1, 3)
            base_alpha = rng.randint(15, 80)
            draw.ellipse(
                (x - size, y - size, x + size, y + size),
                fill=(255, 255, 255, base_alpha),
            )
            if size >= 2 and base_alpha > 40:
                cross_len = size + rng.randint(2, 6)
                cross_alpha = base_alpha // 3
                draw.line(
                    [(x - cross_len, y), (x + cross_len, y)],
                    fill=(255, 255, 255, cross_alpha), width=1,
                )
                draw.line(
                    [(x, y - cross_len), (x, y + cross_len)],
                    fill=(255, 255, 255, cross_alpha), width=1,
                )

        # === Paso 6: Formas geométricas decorativas ===
        if style in ("nebula", "crystal", "electric"):
            for _ in range(10):
                tx = rng.randint(50, w - 50)
                ty = rng.randint(50, h - 50)
                ts = rng.randint(10, 28)
                tri_alpha = rng.randint(8, 22)
                shape = rng.choice(["triangle", "diamond", "square"])
                if shape == "triangle":
                    draw.polygon(
                        [(tx, ty - ts), (tx + ts, ty + ts), (tx - ts, ty + ts)],
                        outline=(*accent, tri_alpha),
                    )
                elif shape == "diamond":
                    draw.polygon(
                        [(tx, ty - ts), (tx + ts, ty), (tx, ty + ts), (tx - ts, ty)],
                        outline=(*accent, tri_alpha),
                    )
                else:
                    draw.rectangle(
                        (tx - ts // 2, ty - ts // 2, tx + ts // 2, ty + ts // 2),
                        outline=(*accent, tri_alpha),
                    )

    def _draw_subtle_pattern(self, draw: ImageDraw.ImageDraw, t: float = 0.0) -> None:
        """Compatibilidad: dibuja el patrón del tema 0 (Nebula Cosmos)."""
        self._draw_themed_pattern(draw, self._BACKGROUND_THEMES[0], seed=42)

    def _draw_text_with_shadow(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        x: int,
        y: int,
        font: ImageFont.FreeTypeFont,
        fill: tuple[int, ...] = (255, 255, 255),
        shadow_color: tuple[int, ...] = (0, 0, 0, 100),
        shadow_offset: int = 3,
    ) -> tuple[int, int]:
        """Dibuja texto con sombra suave.

        Returns:
            (ancho, alto) del texto.
        """
        # Sombra
        draw.text((x + shadow_offset, y + shadow_offset), text,
                  fill=shadow_color, font=font)
        # Texto
        draw.text((x, y), text, fill=fill, font=font)

        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]

    def _draw_text_with_outline(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        x: int,
        y: int,
        font: ImageFont.FreeTypeFont,
        fill: tuple[int, ...] = (255, 255, 255),
        outline_color: tuple[int, ...] = (0, 0, 0),
        outline_width: int = 3,
    ) -> tuple[int, int]:
        """Dibuja texto con outline grueso para máxima legibilidad."""
        for dx in range(-outline_width, outline_width + 1):
            for dy in range(-outline_width, outline_width + 1):
                if dx * dx + dy * dy <= outline_width * outline_width:
                    draw.text((x + dx, y + dy), text, font=font, fill=outline_color)
        draw.text((x, y), text, fill=fill, font=font)

        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]

    def _draw_text_centered(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        y: int,
        font: ImageFont.FreeTypeFont,
        fill: str | tuple = "#FFFFFF",
        max_width: int | None = None,
        shadow: bool = True,
        outline: bool = False,
        outline_width: int = 3,
    ) -> int:
        """Dibuja texto centrado horizontalmente, con ajuste de línea.

        Soporta emojis renderizados con fuente separada.

        Returns:
            La coordenada Y final (después del texto dibujado).
        """
        fill_rgb = self._hex_to_rgb(fill) if isinstance(fill, str) else fill

        effective_max = max_width or (self._width - 120)
        lines = self._wrap_text(text, font, effective_max)

        current_y = y
        for line in lines:
            # Verificar si la línea contiene emojis
            segments = FontManager.split_text_and_emojis(line)
            has_emoji = any(is_em for _, is_em in segments)

            if has_emoji:
                # Renderizar con composición texto + emoji
                current_y = self._draw_line_with_emojis(
                    draw, segments, current_y, font, fill_rgb,
                    shadow=shadow, outline=outline, outline_width=outline_width,
                )
            else:
                bbox = draw.textbbox((0, 0), line, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                x = (self._width - text_width) // 2

                if outline:
                    self._draw_text_with_outline(
                        draw, line, x, current_y, font,
                        fill=fill_rgb, outline_width=outline_width,
                    )
                elif shadow:
                    self._draw_text_with_shadow(
                        draw, line, x, current_y, font, fill=fill_rgb,
                    )
                else:
                    draw.text((x, current_y), line, fill=fill_rgb, font=font)

                current_y += text_height + 10

        return current_y

    def _draw_line_with_emojis(
        self,
        draw: ImageDraw.ImageDraw,
        segments: list[tuple[str, bool]],
        y: int,
        text_font: ImageFont.FreeTypeFont,
        fill: tuple[int, ...],
        shadow: bool = True,
        outline: bool = False,
        outline_width: int = 3,
    ) -> int:
        """Renderiza una línea que mezcla texto y emojis.

        Usa la fuente de texto para caracteres normales y la fuente
        de emojis para emojis, compositeando los resultados.

        Returns:
            Y final después de la línea.
        """
        # Calcular ancho total de la línea
        total_width = 0
        max_height = 0
        segment_widths = []

        emoji_font = self._get_emoji_font(text_font.size)

        for text, is_emoji in segments:
            font = emoji_font if (is_emoji and emoji_font) else text_font
            try:
                bbox = draw.textbbox((0, 0), text, font=font)
                w = bbox[2] - bbox[0]
                h = bbox[3] - bbox[1]
            except Exception:
                # Fallback: usar la fuente de texto normal
                font = text_font
                bbox = draw.textbbox((0, 0), text, font=font)
                w = bbox[2] - bbox[0]
                h = bbox[3] - bbox[1]

            segment_widths.append((w, h, font))
            total_width += w
            max_height = max(max_height, h)

        # Centrar horizontalmente
        x = (self._width - total_width) // 2

        for i, (text, is_emoji) in enumerate(segments):
            w, h, font = segment_widths[i]
            text_y = y + (max_height - h) // 2  # Alinear verticalmente

            if is_emoji and emoji_font:
                try:
                    draw.text((x, text_y), text, font=font, embedded_color=True)
                except Exception:
                    try:
                        draw.text((x, text_y), text, font=font)
                    except Exception:
                        pass
            elif outline:
                self._draw_text_with_outline(
                    draw, text, x, text_y, font,
                    fill=fill, outline_width=outline_width,
                )
            elif shadow:
                self._draw_text_with_shadow(
                    draw, text, x, text_y, font, fill=fill,
                )
            else:
                draw.text((x, text_y), text, fill=fill, font=font)

            x += w

        return y + max_height + 10

    def _wrap_text(
        self,
        text: str,
        font: ImageFont.FreeTypeFont,
        max_width: int,
    ) -> list[str]:
        """Divide texto en líneas que quepan en el ancho máximo."""
        words = text.split()
        lines: list[str] = []
        current_line = ""

        dummy_img = Image.new("RGB", (1, 1))
        dummy_draw = ImageDraw.Draw(dummy_img)

        for word in words:
            test_line = f"{current_line} {word}".strip()
            bbox = dummy_draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        return lines or [text]

    def _draw_rounded_rect(
        self,
        draw: ImageDraw.ImageDraw,
        xy: tuple[int, int, int, int],
        fill: str | tuple,
        radius: int = 20,
        outline: str | tuple | None = None,
        outline_width: int = 2,
    ) -> None:
        """Dibuja un rectángulo con esquinas redondeadas."""
        if isinstance(fill, str):
            fill_color = self._hex_to_rgba(fill) if len(fill) > 0 else (0, 0, 0, 0)
        else:
            fill_color = fill

        if isinstance(outline, str) and outline:
            outline_color = self._hex_to_rgba(outline)
        elif isinstance(outline, tuple):
            outline_color = outline
        else:
            outline_color = None

        draw.rounded_rectangle(
            xy, radius=radius, fill=fill_color,
            outline=outline_color, width=outline_width,
        )

    def _draw_glassmorphism_card(
        self,
        img: Image.Image,
        draw: ImageDraw.ImageDraw,
        xy: tuple[int, int, int, int],
        bg_color: tuple[int, int, int] = (30, 30, 50),
        alpha: int = 180,
        radius: int = 20,
        border_color: tuple[int, int, int] = (108, 92, 231),
        border_alpha: int = 80,
    ) -> None:
        """Dibuja una card con efecto glassmorphism."""
        x1, y1, x2, _y2 = xy

        # Card con transparencia
        draw.rounded_rectangle(
            xy,
            radius=radius,
            fill=(*bg_color, alpha),
            outline=(*border_color, border_alpha),
            width=2,
        )

        # Borde superior brillante sutil
        draw.rounded_rectangle(
            (x1 + 1, y1 + 1, x2 - 1, y1 + 3),
            radius=radius,
            fill=(255, 255, 255, 20),
        )

    def _draw_label_circle(
        self,
        draw: ImageDraw.ImageDraw,
        center_x: int,
        center_y: int,
        label: str,
        font: ImageFont.FreeTypeFont,
        bg_color: tuple[int, int, int] = (108, 92, 231),
        text_color: tuple[int, int, int] = (255, 255, 255),
        radius: int = 22,
    ) -> None:
        """Dibuja una etiqueta (A, B, C, D) dentro de un círculo de color."""
        draw.ellipse(
            (center_x - radius, center_y - radius,
             center_x + radius, center_y + radius),
            fill=(*bg_color, 255),
        )

        bbox = draw.textbbox((0, 0), label, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        draw.text(
            (center_x - tw // 2, center_y - th // 2 - 2),
            label,
            fill=(*text_color, 255),
            font=font,
        )

    # =========================================================================
    # Escenas del Quiz — Diseño Premium
    # =========================================================================

    def render_hook_scene(self, hook_text: str, emoji: str | None = None) -> Image.Image:
        """Renderiza la escena del hook de apertura — diseño impactante.

        Incluye:
        - Fondo gradiente vibrante con patrón
        - Texto grande con outline grueso
        - Emojis gigantes renderizados correctamente
        - Barra decorativa inferior "QUIZ TIME"
        - Elementos decorativos
        """
        img = self._create_gradient_background()
        draw = ImageDraw.Draw(img)

        # === Barra superior decorativa ===
        draw.rounded_rectangle(
            (40, 60, self._width - 40, 68),
            radius=4,
            fill=self._hex_to_rgba(self._colors.primario, 100),
        )

        # === Emoji grande en el centro superior ===
        if emoji:
            emoji_font = self._get_emoji_font(140)
            if emoji_font:
                try:
                    bbox = draw.textbbox((0, 0), emoji, font=emoji_font)
                    emoji_w = bbox[2] - bbox[0]
                    if emoji_w > 10:  # Glyph actually rendered
                        x = (self._width - emoji_w) // 2
                        draw.text(
                            (x, self._height // 2 - 320),
                            emoji, font=emoji_font,
                            embedded_color=True,
                        )
                except Exception:
                    pass
            else:
                # Fallback: decorative glow orb instead of broken square
                cx, cy = self._width // 2, self._height // 2 - 280
                primario = self._hex_to_rgb(self._colors.primario)
                for r in range(55, 0, -5):
                    alpha = int(40 * (1 - r / 55))
                    draw.ellipse(
                        (cx - r, cy - r, cx + r, cy + r),
                        fill=(*primario, alpha),
                    )

        # === Texto del hook — grande y con outline ===
        hook_font = self._get_font(
            self._fonts_config.principal,
            self._fonts_config.tamanio_hook + 8,  # Más grande
        )
        self._draw_text_centered(
            draw, hook_text,
            y=self._height // 2 - 100,
            font=hook_font,
            fill=self._colors.texto,
            outline=True,
            outline_width=4,
        )

        # === Barra "QUIZ TIME" inferior ===
        bar_y = self._height - 300
        bar_color = self._hex_to_rgba(self._colors.primario, 200)
        draw.rounded_rectangle(
            (80, bar_y, self._width - 80, bar_y + 60),
            radius=30,
            fill=bar_color,
        )
        bar_font = self._get_font(self._fonts_config.principal, 28)
        bar_text = "QUIZ TIME"
        bbox = draw.textbbox((0, 0), bar_text, font=bar_font)
        bar_tw = bbox[2] - bbox[0]
        # Decorative diamonds flanking the text
        diamond_s = 8
        diamond_cy = bar_y + 30
        diamond_color = (255, 255, 255, 200)
        for side in [-1, 1]:
            dxx = self._width // 2 + side * (bar_tw // 2 + 28)
            draw.polygon([
                (dxx, diamond_cy - diamond_s), (dxx + diamond_s, diamond_cy),
                (dxx, diamond_cy + diamond_s), (dxx - diamond_s, diamond_cy),
            ], fill=diamond_color)
        draw.text(
            ((self._width - bar_tw) // 2, bar_y + 14),
            bar_text,
            fill=(255, 255, 255, 255),
            font=bar_font,
        )

        # === Indicador "RESPONDE AHORA" ===
        arrow_y = self._height - 180
        arrow_font = self._get_font(self._fonts_config.secundaria, 22)
        arrow_text = "RESPONDE AHORA"
        bbox = draw.textbbox((0, 0), arrow_text, font=arrow_font)
        atw = bbox[2] - bbox[0]
        text_color = self._hex_to_rgba(self._colors.texto_secundario, 150)
        # Small triangle arrows on each side
        tri_s = 7
        for side in [-1, 1]:
            tx = self._width // 2 + side * (atw // 2 + 22)
            ty = arrow_y + 10
            draw.polygon([
                (tx, ty - tri_s), (tx + tri_s * side, ty), (tx, ty + tri_s),
            ], fill=text_color)
        draw.text(
            ((self._width - atw) // 2, arrow_y),
            arrow_text,
            fill=text_color,
            font=arrow_font,
        )

        return img.convert("RGB")

    def render_question_scene(
        self,
        question_number: int,
        total_questions: int,
        question_text: str,
        answers: list[dict[str, Any]],
        timer_value: float | None = None,
        emoji_pista: str | None = None,
        show_correct: bool = False,
        correct_index: int | None = None,
    ) -> Image.Image:
        """Renderiza la escena de una pregunta — diseño premium con zonas fijas.

        Layout por zonas proporcionales (para 1920px de alto):
        - Zona superior  (0-12%):   barra de progreso + badge pregunta + TIMER arriba derecha
        - Zona pregunta  (12-42%):  texto de la pregunta (centrado vertical)
        - Zona opciones  (42-95%):  cards de respuesta distribuidas uniformemente
        """
        img = self._create_gradient_background(
            color_top=self._colors.fondo,
            color_bottom=self._colors.fondo_secundario,
            add_pattern=True,
            theme_index=question_number - 1,
        )
        draw = ImageDraw.Draw(img)

        # =====================================================================
        # Zonas proporcionales fijas (timer ahora en zona superior derecha)
        # =====================================================================
        zone_top_start = 80
        zone_question_start = int(self._height * 0.12)
        zone_options_start = int(self._height * 0.42)
        zone_options_end = int(self._height * 0.94)

        # === ZONA SUPERIOR: Barra de progreso + Badge + Timer ===
        y_cursor = zone_top_start
        self._draw_premium_progress_bar(draw, question_number, total_questions, y=y_cursor)
        y_cursor += 50

        # Badge con número de pregunta (centrado a la izquierda para dejar espacio al timer)
        badge_font = self._get_font(self._fonts_config.principal, 20)
        badge_text = f"PREGUNTA {question_number}/{total_questions}"
        bbox = draw.textbbox((0, 0), badge_text, font=badge_font)
        badge_w = bbox[2] - bbox[0]

        badge_x = 50  # Alineado a la izquierda
        draw.rounded_rectangle(
            (badge_x, y_cursor, badge_x + badge_w + 40, y_cursor + 36),
            radius=18,
            fill=self._hex_to_rgba(self._colors.primario, 160),
        )
        draw.text(
            (badge_x + 20, y_cursor + 6),
            badge_text,
            fill=(255, 255, 255, 255),
            font=badge_font,
        )

        # Timer en la esquina superior derecha
        self._last_timer_y = y_cursor - 10
        if timer_value is not None:
            timer_x = self._width - 120  # Esquina derecha
            self._draw_premium_timer(draw, timer_value, y=y_cursor - 10, center_x=timer_x)

        # === ZONA PREGUNTA: Texto centrado en la zona ===
        question_zone_y = zone_question_start

        # Emoji pista (para Emoji Quiz) — solo si hay fuente emoji
        if emoji_pista:
            emoji_font = self._get_emoji_font(96)
            rendered_emoji = False
            if emoji_font:
                try:
                    bbox = draw.textbbox((0, 0), emoji_pista, font=emoji_font)
                    ew = bbox[2] - bbox[0]
                    if ew > 10:  # Glyph actually rendered (not tofu)
                        draw.text(
                            ((self._width - ew) // 2, question_zone_y),
                            emoji_pista, font=emoji_font,
                            fill=(255, 255, 255, 255),
                        )
                        rendered_emoji = True
                except Exception:
                    pass
            if rendered_emoji:
                question_zone_y += 120

        # Texto de la pregunta — con sombra
        q_font = self._get_font(
            self._fonts_config.principal,
            self._fonts_config.tamanio_pregunta,
        )
        self._draw_text_centered(
            draw, question_text, y=question_zone_y, font=q_font,
            fill=self._colors.texto,
            shadow=True,
            outline=False,
            max_width=self._width - 100,
        )

        # Timer ya se dibuja en la zona superior (arriba), no se repite aquí

        # === ZONA OPCIONES: Cards distribuidas uniformemente ===
        answer_font = self._get_font(
            self._fonts_config.secundaria,
            self._fonts_config.tamanio_respuesta,
        )
        label_font = self._get_font(self._fonts_config.principal, 24)
        labels = ["A", "B", "C", "D"]

        option_height = 80
        num_answers = len(answers)
        available_height = zone_options_end - zone_options_start
        # Distribuir opciones uniformemente en la zona
        if num_answers > 0:
            total_cards_height = num_answers * option_height
            remaining_space = available_height - total_cards_height
            option_margin = max(10, remaining_space // (num_answers + 1))
        else:
            option_margin = 14

        option_start_y = zone_options_start + option_margin

        # Banner "CORRECTO" si estamos en modo reveal
        if show_correct:
            banner_y = option_start_y - 55
            banner_color = self._hex_to_rgba(self._colors.correcto, 220)
            draw.rounded_rectangle(
                (80, banner_y, self._width - 80, banner_y + 48),
                radius=24,
                fill=banner_color,
            )
            banner_font = self._get_font(self._fonts_config.principal, 26)
            banner_text = "CORRECTO"
            bbox = draw.textbbox((0, 0), banner_text, font=banner_font)
            btw = bbox[2] - bbox[0]
            # Draw checkmark as geometric shape
            chk_x = (self._width - btw) // 2 - 32
            chk_cy = banner_y + 24
            draw.line(
                [(chk_x, chk_cy), (chk_x + 8, chk_cy + 10), (chk_x + 22, chk_cy - 8)],
                fill=(255, 255, 255, 255), width=3,
            )
            draw.text(
                ((self._width - btw) // 2, banner_y + 10),
                banner_text,
                fill=(255, 255, 255, 255),
                font=banner_font,
            )

        # Obtener accent del tema activo
        theme = self._BACKGROUND_THEMES[(question_number - 1) % len(self._BACKGROUND_THEMES)]
        theme_accent = theme["accent"]

        for i, answer in enumerate(answers):
            option_y = option_start_y + i * (option_height + option_margin)
            is_correct = (show_correct and (
                i == correct_index or answer.get("es_correcta", False)
            ))
            is_incorrect = show_correct and not is_correct

            # ===== Paleta de colores por estado =====
            # Colores gradiente para el stripe lateral de cada opción
            option_accents = [
                ((108, 92, 231), (160, 120, 255)),   # A: Violeta → Lila
                ((0, 206, 209), (0, 240, 200)),      # B: Turquesa → Menta
                ((255, 105, 180), (255, 160, 200)),   # C: Rosa → Rosa claro
                ((255, 180, 0), (255, 220, 80)),      # D: Naranja → Dorado
            ]
            accent_a, accent_b = option_accents[i % len(option_accents)]

            if is_correct:
                card_bg = self._hex_to_rgb(self._colors.correcto)
                card_alpha = 220
                text_color = (255, 255, 255)
                label_bg = (0, 200, 80)
                border_color_a = (255, 215, 0)
                border_color_b = (0, 255, 130)
                border_width = 4
                shadow_color = (0, 200, 80)
            elif is_incorrect:
                card_bg = (30, 30, 45)
                card_alpha = 80
                text_color = (90, 90, 100)
                label_bg = (50, 50, 60)
                border_color_a = (50, 50, 60)
                border_color_b = (50, 50, 60)
                border_width = 1
                shadow_color = (0, 0, 0)
            else:
                card_bg = (20, 20, 40)
                card_alpha = 210
                text_color = self._hex_to_rgb(self._colors.texto)
                label_bg = accent_a
                border_color_a = accent_a
                border_color_b = accent_b
                border_width = 2
                shadow_color = accent_a

            card_xy = (50, option_y, self._width - 50, option_y + option_height)

            # ===== Sombra coloreada difusa (no negra) =====
            if not is_incorrect:
                for si in range(3, 0, -1):
                    sh_alpha = 20 + si * 10
                    sh_offset = si + 2
                    draw.rounded_rectangle(
                        (50 + si, option_y + sh_offset,
                         self._width - 50 + si, option_y + option_height + sh_offset),
                        radius=16,
                        fill=(*shadow_color, sh_alpha),
                    )

            # ===== Card glassmorphism premium =====
            draw.rounded_rectangle(
                card_xy, radius=18,
                fill=(*card_bg, card_alpha),
            )

            # ===== Borde luminoso con gradiente =====
            # Borde superior (accent_a) → inferior (accent_b)
            bw = border_width
            border_alpha = 200 if is_correct else 120
            # Top border
            draw.rounded_rectangle(
                (50, option_y, self._width - 50, option_y + bw),
                radius=2,
                fill=(*border_color_a, border_alpha),
            )
            # Bottom border
            draw.rounded_rectangle(
                (50, option_y + option_height - bw, self._width - 50, option_y + option_height),
                radius=2,
                fill=(*border_color_b, border_alpha // 2),
            )
            # Left border
            draw.rectangle(
                (50, option_y + bw, 50 + bw, option_y + option_height - bw),
                fill=(*border_color_a, border_alpha // 2),
            )
            # Right border
            draw.rectangle(
                (self._width - 50 - bw, option_y + bw,
                 self._width - 50, option_y + option_height - bw),
                fill=(*border_color_b, border_alpha // 2),
            )

            # ===== Stripe lateral con gradiente multi-color =====
            stripe_w = 6
            for sy in range(option_y, option_y + option_height):
                ratio = (sy - option_y) / max(1, option_height)
                sr = int(accent_a[0] + (accent_b[0] - accent_a[0]) * ratio)
                sg = int(accent_a[1] + (accent_b[1] - accent_a[1]) * ratio)
                sb = int(accent_a[2] + (accent_b[2] - accent_a[2]) * ratio)
                sa = 255 if not is_incorrect else 80
                draw.line(
                    [(50, sy), (50 + stripe_w, sy)],
                    fill=(sr, sg, sb, sa),
                )

            # ===== Inner light effect — brillo superior sutil =====
            if not is_incorrect:
                for iy in range(8):
                    inner_alpha = int(25 * (1 - iy / 8))
                    draw.line(
                        [(52, option_y + 1 + iy), (self._width - 52, option_y + 1 + iy)],
                        fill=(255, 255, 255, inner_alpha),
                    )

            # ===== Glow detrás del label circular =====
            label_cx = 100
            label_cy = option_y + option_height // 2
            if not is_incorrect:
                for gr in range(30, 0, -3):
                    ga = int(15 * (1 - gr / 30))
                    draw.ellipse(
                        (label_cx - gr, label_cy - gr, label_cx + gr, label_cy + gr),
                        fill=(*label_bg, ga),
                    )

            # ===== Check mark para respuesta correcta =====
            if is_correct:
                # Glow detrás del checkmark
                chk_cx = self._width - 88
                chk_cy = option_y + option_height // 2
                for gr in range(20, 0, -2):
                    ga = int(30 * (1 - gr / 20))
                    draw.ellipse(
                        (chk_cx - gr, chk_cy - gr, chk_cx + gr, chk_cy + gr),
                        fill=(0, 255, 130, ga),
                    )
                draw.line(
                    [(chk_cx - 12, chk_cy), (chk_cx - 3, chk_cy + 11),
                     (chk_cx + 14, chk_cy - 11)],
                    fill=(255, 255, 255, 255), width=4,
                )

            # ===== Label circular (A, B, C, D) =====
            label = labels[i] if i < len(labels) else str(i + 1)
            self._draw_label_circle(
                draw,
                center_x=label_cx,
                center_y=label_cy,
                label=label,
                font=label_font,
                bg_color=label_bg,
                radius=22,
            )

            # ===== Texto de la respuesta =====
            answer_text = answer.get('texto', '')

            max_text_width = self._width - 220
            bbox_test = draw.textbbox((0, 0), answer_text, font=answer_font)
            if bbox_test[2] - bbox_test[0] > max_text_width:
                while len(answer_text) > 3:
                    answer_text = answer_text[:-1]
                    bbox_test = draw.textbbox((0, 0), answer_text + "...", font=answer_font)
                    if bbox_test[2] - bbox_test[0] <= max_text_width:
                        answer_text += "..."
                        break

            text_x = 140
            text_y = option_y + (option_height - 30) // 2

            # Sombra de texto
            if not is_incorrect:
                draw.text(
                    (text_x + 2, text_y + 2),
                    answer_text,
                    fill=(0, 0, 0, 90),
                    font=answer_font,
                )

            draw.text(
                (text_x, text_y),
                answer_text,
                fill=(*text_color, 255) if len(text_color) == 3 else text_color,
                font=answer_font,
            )

        # Vignette sutil en modo reveal
        if show_correct:
            self._apply_vignette_overlay(img, intensity=0.3)

        return img.convert("RGB")


    def render_cta_scene(self, cta_text: str) -> Image.Image:
        """Renderiza la escena final con el Call-to-Action — diseño impactante."""
        img = self._create_gradient_background()
        draw = ImageDraw.Draw(img)

        # === Decorative geometric shapes (no emoji dependency) ===
        cx = self._width // 2
        deco_y = self._height // 2 - 240
        primario_rgb = self._hex_to_rgb(self._colors.primario)
        sec_rgb = self._hex_to_rgb(self._colors.secundario)
        # Central glow orb
        for r in range(60, 0, -5):
            alpha = int(45 * (1 - r / 60))
            draw.ellipse(
                (cx - r, deco_y - r, cx + r, deco_y + r),
                fill=(*primario_rgb, alpha),
            )
        # Side accent diamonds
        for dx in [-90, 90]:
            dxx = cx + dx
            draw.polygon([
                (dxx, deco_y - 18), (dxx + 18, deco_y),
                (dxx, deco_y + 18), (dxx - 18, deco_y),
            ], fill=(*sec_rgb, 180))
        # Sparkle dots
        import random as _rng
        _r = _rng.Random(77)
        for _ in range(12):
            sx = cx + _r.randint(-120, 120)
            sy = deco_y + _r.randint(-50, 50)
            ss = _r.randint(2, 5)
            draw.ellipse((sx - ss, sy - ss, sx + ss, sy + ss),
                         fill=(255, 255, 255, _r.randint(40, 100)))

        # === Texto CTA grande con outline ===
        cta_font = self._get_font(
            self._fonts_config.principal,
            self._fonts_config.tamanio_hook + 4,
        )
        self._draw_text_centered(
            draw, cta_text,
            y=self._height // 2 - 80,
            font=cta_font,
            fill=self._colors.texto,
            outline=True,
            outline_width=4,
        )

        # === Barra "LIKE + SUBSCRIBE" ===
        bar_y = self._height // 2 + 100
        draw.rounded_rectangle(
            (100, bar_y, self._width - 100, bar_y + 55),
            radius=28,
            fill=self._hex_to_rgba("#FF0050", 220),
        )
        bar_font = self._get_font(self._fonts_config.principal, 24)
        bar_text = "LIKE + SUBSCRIBE"
        bbox = draw.textbbox((0, 0), bar_text, font=bar_font)
        btw = bbox[2] - bbox[0]
        draw.text(
            ((self._width - btw) // 2, bar_y + 12),
            bar_text,
            fill=(255, 255, 255, 255),
            font=bar_font,
        )

        # === Subtexto ===
        sub_font = self._get_font(self._fonts_config.secundaria, 26)
        self._draw_text_centered(
            draw, "¡Sígueme para más quizzes!",
            y=bar_y + 80,
            font=sub_font,
            fill=self._colors.primario_claro,
        )

        return img.convert("RGB")

    # =========================================================================
    # Elementos UI Premium
    # =========================================================================

    def _draw_premium_progress_bar(
        self,
        draw: ImageDraw.ImageDraw,
        current: int,
        total: int,
        y: int,
    ) -> None:
        """Dibuja una barra de progreso premium con gradiente y glow."""
        bar_margin = 50
        bar_height = 10
        bar_width = self._width - (bar_margin * 2)
        progress = current / total

        # Fondo de la barra (oscuro con borde sutil)
        draw.rounded_rectangle(
            (bar_margin, y, bar_margin + bar_width, y + bar_height),
            radius=5,
            fill=(25, 25, 40, 200),
            outline=(50, 50, 70, 100),
        )

        # Progreso con gradiente
        progress_width = int(bar_width * progress)
        if progress_width > 8:
            # Gradiente horizontal en la barra de progreso
            primario = self._hex_to_rgb(self._colors.primario)
            secundario = self._hex_to_rgb(self._colors.secundario)

            for x in range(progress_width):
                ratio = x / progress_width
                r = int(primario[0] + (secundario[0] - primario[0]) * ratio)
                g = int(primario[1] + (secundario[1] - primario[1]) * ratio)
                b = int(primario[2] + (secundario[2] - primario[2]) * ratio)
                px = bar_margin + x
                draw.line([(px, y + 1), (px, y + bar_height - 1)], fill=(r, g, b, 255))

            # Glow en la punta
            glow_x = bar_margin + progress_width
            for gi in range(8, 0, -1):
                alpha = int(60 * (1 - gi / 8))
                draw.ellipse(
                    (glow_x - gi, y - gi + bar_height // 2,
                     glow_x + gi, y + gi + bar_height // 2),
                    fill=(*secundario, alpha),
                )

    def _draw_premium_timer(
        self,
        draw: ImageDraw.ImageDraw,
        value: float,
        y: int,
        center_x: int | None = None,
    ) -> None:
        """Dibuja el temporizador premium rediseñado — grande, con doble anillo,
        glassmorphism, números con glow, y halo dramático de urgencia."""
        timer_font = self._get_font(
            self._fonts_config.principal,
            58,  # Número grande y legible
        )

        display_value = max(1, math.ceil(value))

        # === Colores según urgencia ===
        if display_value <= 3:
            color = self._hex_to_rgb(self._colors.incorrecto)
            color_secondary = (255, 100, 80)
        elif display_value <= 5:
            color = self._hex_to_rgb(self._colors.advertencia)
            color_secondary = (255, 230, 80)
        else:
            color = self._hex_to_rgb(self._colors.primario)
            color_secondary = (160, 140, 255)

        if center_x is None:
            center_x = self._width // 2
        radius = 55  # Radio más grande para mejor visibilidad
        center_y = y + radius + 8

        # === Halo exterior pulsante ===
        glow_range = 28 if display_value <= 3 else (22 if display_value <= 5 else 16)
        glow_max_alpha = 40 if display_value <= 3 else (25 if display_value <= 5 else 15)
        for gi in range(glow_range, 0, -2):
            glow_alpha = int(glow_max_alpha * (1 - gi / glow_range) ** 0.7)
            glow_r = radius + gi
            draw.ellipse(
                (center_x - glow_r, center_y - glow_r,
                 center_x + glow_r, center_y + glow_r),
                fill=(*color, glow_alpha),
            )

        # === Anillo exterior decorativo (borde brillante fino) ===
        outer_ring_r = radius + 3
        draw.arc(
            (center_x - outer_ring_r, center_y - outer_ring_r,
             center_x + outer_ring_r, center_y + outer_ring_r),
            0, 360,
            fill=(*color, 50),
            width=2,
        )

        # === Fondo glassmorphism (oscuro semi-transparente) ===
        # Anillo exterior de fondo
        draw.ellipse(
            (center_x - radius, center_y - radius,
             center_x + radius, center_y + radius),
            fill=(10, 10, 20, 235),
        )
        # Efecto de brillo interior (glassmorphism)
        for gy in range(radius * 2):
            gx_start = center_x - radius
            actual_y = center_y - radius + gy
            ratio = gy / (radius * 2)
            if ratio < 0.4:
                glass_alpha = int(20 * (1 - ratio / 0.4))
                half_w = int(math.sqrt(max(0, radius ** 2 - (gy - radius) ** 2)))
                if half_w > 0 and glass_alpha > 0:
                    draw.line(
                        [(center_x - half_w, actual_y), (center_x + half_w, actual_y)],
                        fill=(255, 255, 255, glass_alpha),
                    )

        # === Tick marks estilo reloj premium (12 marcas) ===
        for i in range(12):
            angle = math.radians(i * 30 - 90)
            is_major = i % 3 == 0
            inner_r = radius - 12 if is_major else radius - 9
            outer_r = radius - 4
            tick_w = 3 if is_major else 1
            tick_alpha = 200 if is_major else 70
            x1 = center_x + int(inner_r * math.cos(angle))
            y1 = center_y + int(inner_r * math.sin(angle))
            x2 = center_x + int(outer_r * math.cos(angle))
            y2 = center_y + int(outer_r * math.sin(angle))
            draw.line(
                [(x1, y1), (x2, y2)],
                fill=(255, 255, 255, tick_alpha),
                width=tick_w,
            )

        # === Track del arco (anillo oscuro base) ===
        track_r = radius - 6
        draw.arc(
            (center_x - track_r, center_y - track_r,
             center_x + track_r, center_y + track_r),
            0, 360,
            fill=(50, 50, 70, 120),
            width=8,
        )

        # === Arco de progreso con gradiente (doble capa) ===
        progress = max(0.0, min(1.0, value / 10.0))
        arc_angle = int(360 * progress)
        if arc_angle > 0:
            # Capa exterior del arco (color principal)
            draw.arc(
                (center_x - track_r, center_y - track_r,
                 center_x + track_r, center_y + track_r),
                -90, -90 + arc_angle,
                fill=(*color, 255),
                width=8,
            )
            # Capa interior brillante del arco (más clara)
            inner_arc_r = track_r - 2
            draw.arc(
                (center_x - inner_arc_r, center_y - inner_arc_r,
                 center_x + inner_arc_r, center_y + inner_arc_r),
                -90, -90 + arc_angle,
                fill=(*color_secondary, 100),
                width=3,
            )

            # Punto brillante en la punta del arco (más grande y vistoso)
            tip_angle = math.radians(-90 + arc_angle)
            tip_r = track_r
            tip_x = center_x + int(tip_r * math.cos(tip_angle))
            tip_y = center_y + int(tip_r * math.sin(tip_angle))
            # Glow del punto
            for gr in range(12, 0, -2):
                ga = int(60 * (1 - gr / 12))
                draw.ellipse(
                    (tip_x - gr, tip_y - gr, tip_x + gr, tip_y + gr),
                    fill=(*color, ga),
                )
            # Punto blanco brillante
            draw.ellipse(
                (tip_x - 4, tip_y - 4, tip_x + 4, tip_y + 4),
                fill=(255, 255, 255, 230),
            )
            draw.ellipse(
                (tip_x - 2, tip_y - 2, tip_x + 2, tip_y + 2),
                fill=(255, 255, 255, 255),
            )

        # === Anillo interior decorativo con gradiente ===
        inner_deco_r = radius - 18
        draw.arc(
            (center_x - inner_deco_r, center_y - inner_deco_r,
             center_x + inner_deco_r, center_y + inner_deco_r),
            0, 360,
            fill=(*color, 20),
            width=1,
        )

        # === Número centrado con glow ===
        text = str(display_value)
        bbox = draw.textbbox((0, 0), text, font=timer_font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        text_offset_y = bbox[1]
        text_x = center_x - text_w // 2
        text_y_pos = center_y - text_h // 2 - text_offset_y - 3

        # Glow del número (resplandor del color actual)
        for gd in range(4, 0, -1):
            ga = int(40 * (1 - gd / 4))
            for dx in range(-gd, gd + 1):
                for dy in range(-gd, gd + 1):
                    if dx * dx + dy * dy <= gd * gd:
                        draw.text(
                            (text_x + dx, text_y_pos + dy),
                            text, fill=(*color, ga), font=timer_font,
                        )

        # Número principal
        draw.text(
            (text_x, text_y_pos),
            text,
            fill=(*color, 255),
            font=timer_font,
        )

        # === Label "seg" mejorada ===
        label_font = self._get_font(self._fonts_config.secundaria, 14)
        label = "seg"
        lbbox = draw.textbbox((0, 0), label, font=label_font)
        lw = lbbox[2] - lbbox[0]
        draw.text(
            (center_x - lw // 2, center_y + text_h // 2 + 2),
            label,
            fill=(*color_secondary, 180),
            font=label_font,
        )

    def _apply_vignette_overlay(
        self,
        img: Image.Image,
        intensity: float = 0.4,
    ) -> None:
        """Aplica una viñeta oscura sutil in-place sobre una imagen RGBA."""
        import numpy as np
        width, height = img.size
        arr = np.array(img, dtype=np.float64)

        y_grid, x_grid = np.mgrid[0:height, 0:width]
        cx, cy = width / 2, height / 2
        max_radius = math.sqrt(cx ** 2 + cy ** 2)

        dist = np.sqrt((x_grid - cx) ** 2 + (y_grid - cy) ** 2)
        vignette = 1.0 - (dist / max_radius) ** 2 * intensity
        vignette = np.clip(vignette, 0, 1)

        for c in range(min(3, arr.shape[2])):
            arr[:, :, c] *= vignette

        result = np.clip(arr, 0, 255).astype(np.uint8)
        img.paste(Image.fromarray(result))

