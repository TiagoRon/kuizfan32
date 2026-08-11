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

    def _create_gradient_background(
        self,
        color_top: str | None = None,
        color_bottom: str | None = None,
        add_pattern: bool = True,
    ) -> Image.Image:
        """Crea un fondo premium con degradado vertical y patrón sutil."""
        img = Image.new("RGBA", (self._width, self._height))
        draw = ImageDraw.Draw(img)

        top = self._hex_to_rgb(color_top or self._colors.gradiente_inicio)
        bottom = self._hex_to_rgb(color_bottom or self._colors.gradiente_fin)

        # Gradiente principal
        for y in range(self._height):
            ratio = y / self._height
            # Ease-in-out para gradiente más suave
            ratio = ratio * ratio * (3 - 2 * ratio)
            r = int(top[0] + (bottom[0] - top[0]) * ratio)
            g = int(top[1] + (bottom[1] - top[1]) * ratio)
            b = int(top[2] + (bottom[2] - top[2]) * ratio)
            draw.line([(0, y), (self._width, y)], fill=(r, g, b, 255))

        # Patrón geométrico sutil
        if add_pattern:
            self._draw_subtle_pattern(draw)

        return img

    def _draw_subtle_pattern(self, draw: ImageDraw.ImageDraw, t: float = 0.0) -> None:
        """Dibuja un patrón geométrico premium con grid hexagonal y orbs brillantes."""
        import random
        rng = random.Random(42)
        w, h = self._width, self._height

        # Grid de líneas diagonales sutiles
        line_color = (255, 255, 255, 8)
        spacing = 80
        for x in range(-h, w + h, spacing):
            draw.line([(x, 0), (x - h // 2, h)], fill=line_color, width=1)
        for x in range(-h, w + h, spacing):
            draw.line([(x, 0), (x + h // 2, h)], fill=line_color, width=1)

        # Orbs de luz (glow suave)
        for _ in range(8):
            ox = rng.randint(50, w - 50)
            oy = rng.randint(50, h - 50)
            orb_color = rng.choice([
                (108, 92, 231),   # Violeta
                (0, 206, 209),    # Turquesa
                (255, 105, 180),  # Rosa
            ])
            # Glow grande difuso
            for radius in range(60, 0, -5):
                alpha = int(6 * (1 - radius / 60))
                draw.ellipse(
                    (ox - radius, oy - radius, ox + radius, oy + radius),
                    fill=(*orb_color, alpha),
                )

        # Puntos de estrella pequeños
        for _ in range(60):
            x = rng.randint(0, w)
            y = rng.randint(0, h)
            size = rng.randint(1, 3)
            alpha = rng.randint(20, 50)
            draw.ellipse(
                (x - size, y - size, x + size, y + size),
                fill=(255, 255, 255, alpha),
            )

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

        for i, (text, _is_emoji) in enumerate(segments):
            w, h, font = segment_widths[i]
            text_y = y + (max_height - h) // 2  # Alinear verticalmente

            if outline:
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
                            fill=(255, 255, 255, 255),
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
        - Zona superior  (0-15%):   barra de progreso + badge pregunta
        - Zona pregunta  (15-45%):  texto de la pregunta (centrado vertical)
        - Zona timer     (45-55%):  timer circular (posición fija)
        - Zona opciones  (55-95%):  cards de respuesta distribuidas uniformemente
        """
        img = self._create_gradient_background(
            color_top=self._colors.fondo,
            color_bottom=self._colors.fondo_secundario,
            add_pattern=True,
        )
        draw = ImageDraw.Draw(img)

        # =====================================================================
        # Zonas proporcionales fijas (no se solapan nunca)
        # =====================================================================
        zone_top_start = 80
        zone_question_start = int(self._height * 0.15)
        zone_timer_start = int(self._height * 0.44)
        zone_options_start = int(self._height * 0.54)
        zone_options_end = int(self._height * 0.94)

        # === ZONA SUPERIOR: Barra de progreso + Badge ===
        y_cursor = zone_top_start
        self._draw_premium_progress_bar(draw, question_number, total_questions, y=y_cursor)
        y_cursor += 50

        # Badge con número de pregunta
        badge_font = self._get_font(self._fonts_config.principal, 20)
        badge_text = f"PREGUNTA {question_number}/{total_questions}"
        bbox = draw.textbbox((0, 0), badge_text, font=badge_font)
        badge_w = bbox[2] - bbox[0]

        badge_x = (self._width - badge_w - 40) // 2
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

        # === ZONA TIMER: Posición fija, nunca se solapa ===
        # Store timer Y position for countdown clip to use dynamically
        self._last_timer_y = zone_timer_start

        if timer_value is not None:
            self._draw_premium_timer(draw, timer_value, y=zone_timer_start)

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

        for i, answer in enumerate(answers):
            option_y = option_start_y + i * (option_height + option_margin)
            is_correct = (show_correct and (
                i == correct_index or answer.get("es_correcta", False)
            ))
            is_incorrect = show_correct and not is_correct

            # Determinar colores
            if is_correct:
                card_bg = self._hex_to_rgb(self._colors.correcto)
                card_alpha = 220
                text_color = (255, 255, 255)
                label_bg = (0, 200, 80)
                border_color = (255, 215, 0)  # Borde dorado
                border_width = 4
            elif is_incorrect:
                card_bg = (30, 30, 45)
                card_alpha = 80
                text_color = (90, 90, 100)
                label_bg = (50, 50, 60)
                border_color = (50, 50, 60)
                border_width = 1
            else:
                card_bg = (25, 25, 45)
                card_alpha = 200
                text_color = self._hex_to_rgb(self._colors.texto)
                label_bg = self._hex_to_rgb(self._colors.primario)
                border_color = self._hex_to_rgb(self._colors.primario)
                border_width = 2

            # Card con sombra
            card_xy = (50, option_y, self._width - 50, option_y + option_height)

            # Sombra debajo
            if not is_incorrect:
                shadow_xy = (52, option_y + 3, self._width - 48, option_y + option_height + 3)
                draw.rounded_rectangle(
                    shadow_xy, radius=16,
                    fill=(0, 0, 0, 60),
                )

            # Card principal
            draw.rounded_rectangle(
                card_xy, radius=16,
                fill=(*card_bg, card_alpha),
                outline=(*border_color, 200 if is_correct else 100),
                width=border_width,
            )

            # Accent stripe lateral izquierdo
            stripe_color = (*label_bg, 255) if not is_incorrect else (*label_bg, 80)
            draw.rounded_rectangle(
                (50, option_y, 58, option_y + option_height),
                radius=4,
                fill=stripe_color,
            )

            # Brillo superior sutil (solo si no es incorrecta)
            if not is_incorrect:
                draw.rounded_rectangle(
                    (52, option_y + 1, self._width - 52, option_y + 3),
                    radius=2,
                    fill=(255, 255, 255, 15),
                )

            # Check mark grande para respuesta correcta
            if is_correct:
                # Draw checkmark as geometric lines (no Unicode dependency)
                chk_cx = self._width - 88
                chk_cy = option_y + option_height // 2
                draw.line(
                    [(chk_cx - 12, chk_cy), (chk_cx - 3, chk_cy + 11),
                     (chk_cx + 14, chk_cy - 11)],
                    fill=(255, 255, 255, 255), width=4,
                )

            # Label circular (A, B, C, D)
            label = labels[i] if i < len(labels) else str(i + 1)
            self._draw_label_circle(
                draw,
                center_x=100,
                center_y=option_y + option_height // 2,
                label=label,
                font=label_font,
                bg_color=label_bg,
                radius=20,
            )

            # Texto de la respuesta SIN emojis (para evitar encoding issues)
            answer_text = answer.get('texto', '')

            # Truncar si es muy largo
            max_text_width = self._width - 200
            bbox_test = draw.textbbox((0, 0), answer_text, font=answer_font)
            if bbox_test[2] - bbox_test[0] > max_text_width:
                while len(answer_text) > 3:
                    answer_text = answer_text[:-1]
                    bbox_test = draw.textbbox((0, 0), answer_text + "...", font=answer_font)
                    if bbox_test[2] - bbox_test[0] <= max_text_width:
                        answer_text += "..."
                        break

            text_x = 135
            text_y = option_y + (option_height - 30) // 2

            # Sombra de texto
            if not is_incorrect:
                draw.text(
                    (text_x + 2, text_y + 2),
                    answer_text,
                    fill=(0, 0, 0, 80),
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
    ) -> None:
        """Dibuja el temporizador circular premium — centrado, con glow."""
        timer_font = self._get_font(
            self._fonts_config.principal,
            self._fonts_config.tamanio_timer,
        )

        display_value = max(1, math.ceil(value))

        if display_value <= 3:
            color = self._hex_to_rgb(self._colors.incorrecto)
        elif display_value <= 5:
            color = self._hex_to_rgb(self._colors.advertencia)
        else:
            color = self._hex_to_rgb(self._colors.primario)

        center_x = self._width // 2
        radius = 50  # Más compacto para no solaparse
        center_y = y + radius

        # Glow del arco (halo difuso)
        for gi in range(12, 0, -2):
            glow_alpha = int(20 * (1 - gi / 12))
            glow_r = radius + gi
            draw.arc(
                (center_x - glow_r, center_y - glow_r,
                 center_x + glow_r, center_y + glow_r),
                0, 360,
                fill=(*color, glow_alpha),
                width=3,
            )

        # Fondo del timer (anillo oscuro)
        draw.arc(
            (center_x - radius, center_y - radius,
             center_x + radius, center_y + radius),
            0, 360,
            fill=(45, 45, 58, 200),
            width=8,
        )

        # Arco de progreso
        progress = max(0.0, min(1.0, value / 10.0))
        arc_angle = int(360 * progress)
        if arc_angle > 0:
            draw.arc(
                (center_x - radius, center_y - radius,
                 center_x + radius, center_y + radius),
                -90, -90 + arc_angle,
                fill=(*color, 255),
                width=8,
            )

        # Número centrado correctamente
        text = str(display_value)
        bbox = draw.textbbox((0, 0), text, font=timer_font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        # Compensar offset de ascender de la fuente
        text_offset_y = bbox[1]
        draw.text(
            (center_x - text_w // 2, center_y - text_h // 2 - text_offset_y),
            text,
            fill=(*color, 255),
            font=timer_font,
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

