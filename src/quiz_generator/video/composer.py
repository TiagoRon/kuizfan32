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
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFilter, ImageFont

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

    def _draw_subtle_pattern(self, draw: ImageDraw.ImageDraw) -> None:
        """Dibuja un patrón decorativo sutil en el fondo."""
        import random
        rng = random.Random(42)
        # Puntos sutiles
        for _ in range(40):
            x = rng.randint(0, self._width)
            y = rng.randint(0, self._height)
            size = rng.randint(1, 3)
            alpha = rng.randint(10, 30)
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
        if isinstance(fill, str):
            fill_rgb = self._hex_to_rgb(fill)
        else:
            fill_rgb = fill

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
        x1, y1, x2, y2 = xy

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
            text_font = self._get_font(self._fonts_config.principal, 140)
            display_font = emoji_font or text_font

            try:
                bbox = draw.textbbox((0, 0), emoji, font=display_font)
                emoji_w = bbox[2] - bbox[0]
                x = (self._width - emoji_w) // 2
                draw.text(
                    (x, self._height // 2 - 320),
                    emoji, font=display_font,
                    fill=(255, 255, 255, 255),
                )
            except Exception:
                pass  # Emoji no renderizable, continuar

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
        bar_text = "⚡ QUIZ TIME ⚡"
        bbox = draw.textbbox((0, 0), bar_text, font=bar_font)
        bar_tw = bbox[2] - bbox[0]
        draw.text(
            ((self._width - bar_tw) // 2, bar_y + 14),
            bar_text,
            fill=(255, 255, 255, 255),
            font=bar_font,
        )

        # === Flecha/indicador de "swipe up" ===
        arrow_y = self._height - 180
        arrow_font = self._get_font(self._fonts_config.secundaria, 22)
        arrow_text = "▲ RESPONDE AHORA ▲"
        bbox = draw.textbbox((0, 0), arrow_text, font=arrow_font)
        atw = bbox[2] - bbox[0]
        draw.text(
            ((self._width - atw) // 2, arrow_y),
            arrow_text,
            fill=self._hex_to_rgba(self._colors.texto_secundario, 150),
            font=arrow_font,
        )

        return img.convert("RGB")

    def render_question_scene(
        self,
        question_number: int,
        total_questions: int,
        question_text: str,
        answers: list[dict[str, Any]],
        timer_value: int | None = None,
        emoji_pista: str | None = None,
        show_correct: bool = False,
        correct_index: int | None = None,
    ) -> Image.Image:
        """Renderiza la escena de una pregunta — diseño premium.

        Incluye:
        - Barra de progreso con gradiente y glow
        - Badge circular con número de pregunta
        - Texto de pregunta con sombra
        - Cards glassmorphism para opciones
        - Labels en círculos de color (A, B, C, D)
        - Timer circular con arco animado
        """
        img = self._create_gradient_background(
            color_top=self._colors.fondo,
            color_bottom=self._colors.fondo_secundario,
            add_pattern=True,
        )
        draw = ImageDraw.Draw(img)

        y_cursor = 80

        # === Barra de progreso premium ===
        self._draw_premium_progress_bar(draw, question_number, total_questions, y=y_cursor)
        y_cursor += 50

        # === Badge con número de pregunta ===
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
        y_cursor += 60

        # === Emoji pista (para Emoji Quiz) ===
        if emoji_pista:
            emoji_font = self._get_emoji_font(96)
            text_font = self._get_font(self._fonts_config.principal, 96)
            font_to_use = emoji_font or text_font

            try:
                bbox = draw.textbbox((0, 0), emoji_pista, font=font_to_use)
                ew = bbox[2] - bbox[0]
                draw.text(
                    ((self._width - ew) // 2, y_cursor),
                    emoji_pista, font=font_to_use,
                    fill=(255, 255, 255, 255),
                )
            except Exception:
                pass
            y_cursor += 130

        # === Texto de la pregunta — con sombra ===
        q_font = self._get_font(
            self._fonts_config.principal,
            self._fonts_config.tamanio_pregunta,
        )
        y_cursor = self._draw_text_centered(
            draw, question_text, y=y_cursor, font=q_font,
            fill=self._colors.texto,
            shadow=True,
            outline=False,
        )
        y_cursor += 30

        # === Temporizador circular ===
        if timer_value is not None:
            self._draw_premium_timer(draw, timer_value, y=y_cursor)
            y_cursor += 100

        # === Opciones de respuesta en cards premium ===
        answer_font = self._get_font(
            self._fonts_config.secundaria,
            self._fonts_config.tamanio_respuesta,
        )
        label_font = self._get_font(self._fonts_config.principal, 24)
        labels = ["A", "B", "C", "D"]

        option_height = 80
        option_margin = 14
        total_options_height = len(answers) * (option_height + option_margin)
        option_start_y = max(
            y_cursor + 10,
            self._height - total_options_height - 80,
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
                card_alpha = 200
                text_color = (0, 0, 0)
                label_bg = (0, 200, 80)
                border_color = self._hex_to_rgb(self._colors.correcto)
            elif is_incorrect:
                card_bg = (40, 40, 55)
                card_alpha = 120
                text_color = (130, 130, 140)
                label_bg = (60, 60, 75)
                border_color = (60, 60, 75)
            else:
                card_bg = (30, 30, 50)
                card_alpha = 180
                text_color = self._hex_to_rgb(self._colors.texto)
                label_bg = self._hex_to_rgb(self._colors.primario)
                border_color = self._hex_to_rgb(self._colors.primario)

            # Card glassmorphism
            card_xy = (50, option_y, self._width - 50, option_y + option_height)
            self._draw_glassmorphism_card(
                img, draw, card_xy,
                bg_color=card_bg,
                alpha=card_alpha,
                radius=16,
                border_color=border_color,
                border_alpha=100 if not show_correct else 180,
            )

            # Check mark para respuesta correcta
            if is_correct:
                check_font = self._get_font(self._fonts_config.principal, 32)
                draw.text(
                    (self._width - 100, option_y + 20),
                    "✓",
                    fill=(255, 255, 255, 255),
                    font=check_font,
                )

            # Label circular (A, B, C, D)
            label = labels[i] if i < len(labels) else str(i + 1)
            self._draw_label_circle(
                draw,
                center_x=95,
                center_y=option_y + option_height // 2,
                label=label,
                font=label_font,
                bg_color=label_bg,
                radius=20,
            )

            # Texto de la respuesta con emoji
            emoji_prefix = f"{answer.get('emoji', '')} " if answer.get("emoji") else ""
            answer_text = f"{emoji_prefix}{answer.get('texto', '')}"

            # Renderizar con soporte emoji
            segments = FontManager.split_text_and_emojis(answer_text)
            text_x = 130
            text_y = option_y + (option_height - 30) // 2

            for seg_text, is_emoji in segments:
                if is_emoji:
                    emoji_f = self._get_emoji_font(answer_font.size)
                    seg_font = emoji_f or answer_font
                else:
                    seg_font = answer_font

                try:
                    draw.text(
                        (text_x, text_y),
                        seg_text,
                        fill=(*text_color, 255) if len(text_color) == 3 else text_color,
                        font=seg_font,
                    )
                    bbox = draw.textbbox((0, 0), seg_text, font=seg_font)
                    text_x += bbox[2] - bbox[0]
                except Exception:
                    draw.text(
                        (text_x, text_y),
                        seg_text,
                        fill=(*text_color, 255) if len(text_color) == 3 else text_color,
                        font=answer_font,
                    )
                    bbox = draw.textbbox((0, 0), seg_text, font=answer_font)
                    text_x += bbox[2] - bbox[0]

        return img.convert("RGB")

    def render_cta_scene(self, cta_text: str) -> Image.Image:
        """Renderiza la escena final con el Call-to-Action — diseño impactante."""
        img = self._create_gradient_background()
        draw = ImageDraw.Draw(img)

        # === Emojis decorativos gigantes ===
        emoji_text = "🎯🔥⭐"
        emoji_font = self._get_emoji_font(80)
        text_font = self._get_font(self._fonts_config.principal, 80)
        display_font = emoji_font or text_font

        try:
            bbox = draw.textbbox((0, 0), emoji_text, font=display_font)
            ew = bbox[2] - bbox[0]
            draw.text(
                ((self._width - ew) // 2, self._height // 2 - 250),
                emoji_text,
                font=display_font,
                fill=(255, 255, 255, 255),
            )
        except Exception:
            pass

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
        bar_text = "❤️ LIKE + SUBSCRIBE ❤️"
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
        value: int,
        y: int,
    ) -> None:
        """Dibuja el temporizador circular premium."""
        timer_font = self._get_font(
            self._fonts_config.principal,
            self._fonts_config.tamanio_timer,
        )

        # Color según tiempo restante
        if value <= 3:
            color = self._hex_to_rgb(self._colors.incorrecto)
        elif value <= 5:
            color = self._hex_to_rgb(self._colors.advertencia)
        else:
            color = self._hex_to_rgb(self._colors.primario)

        center_x = self._width // 2
        radius = 45

        # Fondo del timer (anillo oscuro)
        draw.arc(
            (center_x - radius, y, center_x + radius, y + radius * 2),
            0, 360,
            fill=(45, 45, 58, 200),
            width=6,
        )

        # Arco de progreso (basado en el valor del timer)
        arc_angle = int(360 * (value / 10))
        if arc_angle > 0:
            draw.arc(
                (center_x - radius, y, center_x + radius, y + radius * 2),
                -90, -90 + arc_angle,
                fill=(*color, 255),
                width=6,
            )

        # Número centrado
        text = str(value)
        bbox = draw.textbbox((0, 0), text, font=timer_font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        draw.text(
            (center_x - text_w // 2, y + radius - text_h // 2),
            text,
            fill=(*color, 255),
            font=timer_font,
        )
