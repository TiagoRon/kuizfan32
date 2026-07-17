"""Compositor de escenas — genera fotogramas con Pillow.

Crea las imágenes/fotogramas de cada escena del quiz usando
Pillow para renderizar texto, fondos, opciones, temporizadores,
barras de progreso y otros elementos visuales.

Evita usar TextClip de MoviePy (lento) — genera imágenes con
Pillow y las convierte a clips de video.
"""

from __future__ import annotations

import logging
import math
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from quiz_generator.config import Settings

logger = logging.getLogger(__name__)

# Fuente por defecto si no se encuentra la configurada
_FALLBACK_FONT = "arial.ttf"


class SceneComposer:
    """Compositor de escenas visuales usando Pillow.

    Genera imágenes de alta calidad para cada fotograma del video,
    incluyendo fondos degradados, texto estilizado, opciones de
    respuesta, temporizadores y efectos visuales.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._width = settings.video.ancho
        self._height = settings.video.alto
        self._colors = settings.video.colores
        self._fonts_config = settings.video.fuentes
        self._fonts_cache: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}

    def _get_font(self, family: str, size: int) -> ImageFont.FreeTypeFont:
        """Obtiene una fuente, con caché y fallback."""
        key = (family, size)
        if key not in self._fonts_cache:
            try:
                self._fonts_cache[key] = ImageFont.truetype(family, size)
            except OSError:
                try:
                    self._fonts_cache[key] = ImageFont.truetype(_FALLBACK_FONT, size)
                except OSError:
                    self._fonts_cache[key] = ImageFont.load_default(size)
        return self._fonts_cache[key]

    def _hex_to_rgb(self, hex_color: str) -> tuple[int, int, int]:
        """Convierte color hexadecimal a tupla RGB."""
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))  # type: ignore[return-value]

    def _create_gradient_background(
        self,
        color_top: str | None = None,
        color_bottom: str | None = None,
    ) -> Image.Image:
        """Crea un fondo con degradado vertical."""
        img = Image.new("RGB", (self._width, self._height))
        draw = ImageDraw.Draw(img)

        top = self._hex_to_rgb(color_top or self._colors.gradiente_inicio)
        bottom = self._hex_to_rgb(color_bottom or self._colors.gradiente_fin)

        for y in range(self._height):
            ratio = y / self._height
            r = int(top[0] + (bottom[0] - top[0]) * ratio)
            g = int(top[1] + (bottom[1] - top[1]) * ratio)
            b = int(top[2] + (bottom[2] - top[2]) * ratio)
            draw.line([(0, y), (self._width, y)], fill=(r, g, b))

        return img

    def _draw_text_centered(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        y: int,
        font: ImageFont.FreeTypeFont,
        fill: str = "#FFFFFF",
        max_width: int | None = None,
    ) -> int:
        """Dibuja texto centrado horizontalmente, con ajuste de línea.

        Returns:
            La coordenada Y final (después del texto dibujado).
        """
        effective_max = max_width or (self._width - 120)
        fill_rgb = self._hex_to_rgb(fill)

        # Dividir en líneas si el texto es muy largo
        lines = self._wrap_text(text, font, effective_max)

        current_y = y
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (self._width - text_width) // 2
            draw.text((x, current_y), line, fill=fill_rgb, font=font)
            current_y += text_height + 8  # Espaciado entre líneas

        return current_y

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
        fill: str,
        radius: int = 20,
        outline: str | None = None,
        outline_width: int = 2,
    ) -> None:
        """Dibuja un rectángulo con esquinas redondeadas."""
        fill_rgb = self._hex_to_rgb(fill)
        outline_rgb = self._hex_to_rgb(outline) if outline else None
        draw.rounded_rectangle(
            xy, radius=radius, fill=fill_rgb,
            outline=outline_rgb, width=outline_width,
        )

    # =========================================================================
    # Escenas del Quiz
    # =========================================================================

    def render_hook_scene(self, hook_text: str, emoji: str | None = None) -> Image.Image:
        """Renderiza la escena del hook de apertura."""
        img = self._create_gradient_background()
        draw = ImageDraw.Draw(img)

        # Emoji grande en el centro superior
        if emoji:
            emoji_font = self._get_font(self._fonts_config.emoji, 120)
            bbox = draw.textbbox((0, 0), emoji, font=emoji_font)
            emoji_w = bbox[2] - bbox[0]
            draw.text(
                ((self._width - emoji_w) // 2, self._height // 2 - 250),
                emoji, font=emoji_font, fill=(255, 255, 255),
            )

        # Texto del hook
        hook_font = self._get_font(
            self._fonts_config.principal,
            self._fonts_config.tamanio_hook,
        )
        self._draw_text_centered(
            draw, hook_text,
            y=self._height // 2 - 60,
            font=hook_font,
            fill=self._colors.texto,
        )

        return img

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
        """Renderiza la escena de una pregunta con sus opciones.

        Args:
            question_number: Número de la pregunta (1-indexed).
            total_questions: Total de preguntas en el quiz.
            question_text: Texto de la pregunta.
            answers: Lista de dicts con 'texto', 'emoji', 'es_correcta'.
            timer_value: Valor actual del temporizador (None = no mostrar).
            emoji_pista: Emojis como pista (para Emoji Quiz).
            show_correct: Si mostrar cuál es la respuesta correcta.
            correct_index: Índice de la respuesta correcta.

        Returns:
            Imagen PIL de la escena.
        """
        img = self._create_gradient_background(
            color_top=self._colors.fondo,
            color_bottom=self._colors.fondo_secundario,
        )
        draw = ImageDraw.Draw(img)

        y_cursor = 80

        # -- Barra de progreso superior --
        self._draw_progress_bar(draw, question_number, total_questions, y=y_cursor)
        y_cursor += 50

        # -- Número de pregunta --
        num_font = self._get_font(self._fonts_config.secundaria, 28)
        self._draw_text_centered(
            draw,
            f"Pregunta {question_number} de {total_questions}",
            y=y_cursor,
            font=num_font,
            fill=self._colors.texto_secundario,
        )
        y_cursor += 60

        # -- Emoji pista (para Emoji Quiz) --
        if emoji_pista:
            emoji_font = self._get_font(self._fonts_config.emoji, 96)
            self._draw_text_centered(
                draw, emoji_pista, y=y_cursor, font=emoji_font,
            )
            y_cursor += 140

        # -- Texto de la pregunta --
        q_font = self._get_font(
            self._fonts_config.principal,
            self._fonts_config.tamanio_pregunta,
        )
        y_cursor = self._draw_text_centered(
            draw, question_text, y=y_cursor, font=q_font,
            fill=self._colors.texto,
        )
        y_cursor += 40

        # -- Temporizador --
        if timer_value is not None:
            self._draw_timer(draw, timer_value, y=y_cursor)
            y_cursor += 100

        # -- Opciones de respuesta --
        answer_font = self._get_font(
            self._fonts_config.secundaria,
            self._fonts_config.tamanio_respuesta,
        )
        labels = ["A", "B", "C", "D"]

        option_height = 80
        option_margin = 12
        option_start_y = max(y_cursor, self._height - (len(answers) * (option_height + option_margin)) - 120)

        for i, answer in enumerate(answers):
            option_y = option_start_y + i * (option_height + option_margin)

            # Determinar color de fondo
            if show_correct and i == correct_index:
                bg_color = self._colors.correcto
                text_color = self._colors.texto_oscuro
            elif show_correct and answer.get("es_correcta"):
                bg_color = self._colors.correcto
                text_color = self._colors.texto_oscuro
            elif show_correct:
                bg_color = self._colors.incorrecto
                text_color = self._colors.texto
            else:
                bg_color = self._colors.fondo_secundario
                text_color = self._colors.texto

            # Rectángulo de la opción
            self._draw_rounded_rect(
                draw,
                (60, option_y, self._width - 60, option_y + option_height),
                fill=bg_color,
                radius=16,
                outline=self._colors.primario if not show_correct else None,
            )

            # Label (A, B, C, D)
            label = labels[i] if i < len(labels) else str(i + 1)
            label_font = self._get_font(self._fonts_config.principal, 32)
            draw.text(
                (90, option_y + 20),
                f"{label})",
                fill=self._hex_to_rgb(self._colors.primario_claro if not show_correct else text_color),
                font=label_font,
            )

            # Texto de la respuesta
            emoji_prefix = f"{answer.get('emoji', '')} " if answer.get("emoji") else ""
            answer_text = f"{emoji_prefix}{answer.get('texto', '')}"
            draw.text(
                (150, option_y + 22),
                answer_text,
                fill=self._hex_to_rgb(text_color),
                font=answer_font,
            )

        return img

    def render_curiosity_scene(
        self,
        curiosity_text: str,
        correct_answer: str,
    ) -> Image.Image:
        """Renderiza la escena del dato curioso después de la respuesta."""
        img = self._create_gradient_background(
            color_top="#0A2463",
            color_bottom="#1E1E2E",
        )
        draw = ImageDraw.Draw(img)

        # Icono de dato curioso
        icon_font = self._get_font(self._fonts_config.emoji, 80)
        self._draw_text_centered(draw, "💡", y=self._height // 2 - 200, font=icon_font)

        # Título
        title_font = self._get_font(self._fonts_config.principal, 36)
        self._draw_text_centered(
            draw, "¿Sabías que...?",
            y=self._height // 2 - 100,
            font=title_font,
            fill=self._colors.advertencia,
        )

        # Dato curioso
        body_font = self._get_font(self._fonts_config.secundaria, 32)
        self._draw_text_centered(
            draw, curiosity_text,
            y=self._height // 2,
            font=body_font,
            fill=self._colors.texto,
        )

        return img

    def render_cta_scene(self, cta_text: str) -> Image.Image:
        """Renderiza la escena final con el Call-to-Action."""
        img = self._create_gradient_background()
        draw = ImageDraw.Draw(img)

        # Emojis decorativos
        emoji_font = self._get_font(self._fonts_config.emoji, 72)
        self._draw_text_centered(draw, "🎯🔥⭐", y=self._height // 2 - 200, font=emoji_font)

        # Texto CTA
        cta_font = self._get_font(
            self._fonts_config.principal,
            self._fonts_config.tamanio_hook,
        )
        self._draw_text_centered(
            draw, cta_text,
            y=self._height // 2 - 40,
            font=cta_font,
            fill=self._colors.texto,
        )

        # Subtexto
        sub_font = self._get_font(self._fonts_config.secundaria, 28)
        self._draw_text_centered(
            draw, "¡Sígueme para más quizzes!",
            y=self._height // 2 + 120,
            font=sub_font,
            fill=self._colors.primario_claro,
        )

        return img

    # =========================================================================
    # Elementos UI
    # =========================================================================

    def _draw_progress_bar(
        self,
        draw: ImageDraw.ImageDraw,
        current: int,
        total: int,
        y: int,
    ) -> None:
        """Dibuja una barra de progreso en la parte superior."""
        bar_margin = 40
        bar_height = 8
        bar_width = self._width - (bar_margin * 2)
        progress = current / total

        # Fondo de la barra
        self._draw_rounded_rect(
            draw,
            (bar_margin, y, bar_margin + bar_width, y + bar_height),
            fill=self._colors.texto_oscuro,
            radius=4,
        )

        # Progreso
        progress_width = int(bar_width * progress)
        if progress_width > 0:
            self._draw_rounded_rect(
                draw,
                (bar_margin, y, bar_margin + progress_width, y + bar_height),
                fill=self._colors.primario,
                radius=4,
            )

    def _draw_timer(
        self,
        draw: ImageDraw.ImageDraw,
        value: int,
        y: int,
    ) -> None:
        """Dibuja el temporizador circular."""
        timer_font = self._get_font(
            self._fonts_config.principal,
            self._fonts_config.tamanio_timer,
        )

        # Color según el tiempo restante
        if value <= 3:
            color = self._colors.incorrecto
        elif value <= 5:
            color = self._colors.advertencia
        else:
            color = self._colors.primario

        # Círculo del timer
        center_x = self._width // 2
        radius = 45

        draw.ellipse(
            (center_x - radius, y - radius + 45, center_x + radius, y + radius + 45),
            outline=self._hex_to_rgb(color),
            width=4,
        )

        # Número
        text = str(value)
        bbox = draw.textbbox((0, 0), text, font=timer_font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        draw.text(
            (center_x - text_w // 2, y + 45 - text_h // 2 - 5),
            text,
            fill=self._hex_to_rgb(color),
            font=timer_font,
        )
