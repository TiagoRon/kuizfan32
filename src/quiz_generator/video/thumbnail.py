"""Generador de miniaturas virales para videos de quiz.

Crea miniaturas estilo clickbait de alta calidad con Pillow:
texto grande con outline, emojis decorativos gigantes,
fondos gradiente vibrantes y composición visual impactante.
"""

from __future__ import annotations

import logging
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from quiz_generator.config import Settings
from quiz_generator.core.models import Quiz, ThumbnailSpec

logger = logging.getLogger(__name__)

_FALLBACK_FONT = "arial.ttf"


class ThumbnailGenerator:
    """Generador de miniaturas para videos de quiz.

    Crea imágenes 1080×1920 (vertical) o 1280×720 (horizontal) con
    estilo clickbait viral: texto grande, colores vibrantes, emojis
    y efectos de sombra/outline.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._fonts_cache: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}

    def _get_font(self, family: str, size: int) -> ImageFont.FreeTypeFont:
        """Obtiene una fuente con caché y fallback."""
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
        return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]

    def _create_gradient(
        self,
        width: int,
        height: int,
        color_top: tuple[int, int, int],
        color_bottom: tuple[int, int, int],
    ) -> Image.Image:
        """Crea un fondo con degradado vertical."""
        img = Image.new("RGB", (width, height))
        draw = ImageDraw.Draw(img)

        for y in range(height):
            ratio = y / height
            r = int(color_top[0] + (color_bottom[0] - color_top[0]) * ratio)
            g = int(color_top[1] + (color_bottom[1] - color_top[1]) * ratio)
            b = int(color_top[2] + (color_bottom[2] - color_top[2]) * ratio)
            draw.line([(0, y), (width, y)], fill=(r, g, b))

        return img

    def _draw_text_with_outline(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        x: int,
        y: int,
        font: ImageFont.FreeTypeFont,
        fill: tuple[int, int, int] = (255, 255, 255),
        outline_color: tuple[int, int, int] = (0, 0, 0),
        outline_width: int = 4,
    ) -> tuple[int, int]:
        """Dibuja texto con outline negro para máxima legibilidad.

        Returns:
            Tupla (ancho, alto) del texto dibujado.
        """
        # Outline
        for dx in range(-outline_width, outline_width + 1):
            for dy in range(-outline_width, outline_width + 1):
                if dx * dx + dy * dy <= outline_width * outline_width:
                    draw.text((x + dx, y + dy), text, font=font, fill=outline_color)

        # Texto principal
        draw.text((x, y), text, font=font, fill=fill)

        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]

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

    def generate(
        self,
        quiz: Quiz,
        output_path: Path,
        spec: ThumbnailSpec | None = None,
    ) -> Path:
        """Genera una miniatura viral para un quiz.

        Args:
            quiz: El quiz para el que generar la miniatura.
            output_path: Ruta donde guardar la miniatura (PNG).
            spec: Especificación opcional de la miniatura.

        Returns:
            Ruta al archivo de miniatura generado.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Usar spec proporcionada o generar una por defecto
        if spec is None:
            spec = ThumbnailSpec(
                texto_principal=quiz.metadata.titulo,
                texto_secundario=quiz.hook.texto,
                emojis=[quiz.hook.emoji] if quiz.hook.emoji else ["🧠", "🔥"],
            )

        width = spec.ancho
        height = spec.alto
        colors = self._settings.video.colores

        # 1. Fondo gradiente vibrante
        top_color = self._hex_to_rgb(colors.gradiente_inicio)
        bottom_color = self._hex_to_rgb(colors.gradiente_fin)
        img = self._create_gradient(width, height, top_color, bottom_color)
        draw = ImageDraw.Draw(img)

        # 2. Emojis decorativos gigantes (arriba)
        emoji_font = self._get_font(
            self._settings.video.fuentes.emoji, 140,
        )
        emojis_text = " ".join(spec.emojis[:3]) if spec.emojis else "🧠🔥"
        bbox = draw.textbbox((0, 0), emojis_text, font=emoji_font)
        emoji_w = bbox[2] - bbox[0]
        draw.text(
            ((width - emoji_w) // 2, height // 5),
            emojis_text,
            font=emoji_font,
            fill=(255, 255, 255),
        )

        # 3. Texto principal grande con outline
        title_font = self._get_font(
            self._settings.video.fuentes.principal, 72,
        )
        lines = self._wrap_text(spec.texto_principal, title_font, width - 120)
        y_pos = height // 2 - (len(lines) * 85) // 2

        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=title_font)
            line_w = bbox[2] - bbox[0]
            x_pos = (width - line_w) // 2
            self._draw_text_with_outline(
                draw, line, x_pos, y_pos, title_font,
                fill=(255, 255, 255),
                outline_color=(0, 0, 0),
                outline_width=5,
            )
            y_pos += 85

        # 4. Texto secundario (subtítulo)
        if spec.texto_secundario:
            sub_font = self._get_font(
                self._settings.video.fuentes.secundaria, 40,
            )
            sub_lines = self._wrap_text(spec.texto_secundario, sub_font, width - 160)
            y_sub = y_pos + 40

            for line in sub_lines:
                bbox = draw.textbbox((0, 0), line, font=sub_font)
                line_w = bbox[2] - bbox[0]
                x_pos = (width - line_w) // 2
                self._draw_text_with_outline(
                    draw, line, x_pos, y_sub, sub_font,
                    fill=self._hex_to_rgb(colors.primario_claro),
                    outline_color=(0, 0, 0),
                    outline_width=3,
                )
                y_sub += 55

        # 5. Barra decorativa inferior
        bar_color = self._hex_to_rgb(colors.primario)
        draw.rounded_rectangle(
            (60, height - 200, width - 60, height - 160),
            radius=20,
            fill=bar_color,
        )
        bar_font = self._get_font(
            self._settings.video.fuentes.principal, 32,
        )
        bar_text = f"❓ {len(quiz.preguntas)} PREGUNTAS"
        bbox = draw.textbbox((0, 0), bar_text, font=bar_font)
        bar_text_w = bbox[2] - bbox[0]
        draw.text(
            ((width - bar_text_w) // 2, height - 195),
            bar_text,
            font=bar_font,
            fill=(255, 255, 255),
        )

        # Guardar
        img.save(str(output_path), "PNG", quality=95)
        logger.info("Miniatura generada: %s", output_path)

        return output_path

    def generate_from_spec(
        self,
        spec: ThumbnailSpec,
        output_path: Path,
    ) -> Path:
        """Genera una miniatura directamente desde una especificación.

        Útil cuando no se tiene un Quiz completo pero sí los datos
        para la miniatura.

        Args:
            spec: Especificación de la miniatura.
            output_path: Ruta de salida.

        Returns:
            Ruta al archivo generado.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        width = spec.ancho
        height = spec.alto

        top_color = self._hex_to_rgb(spec.color_fondo)
        bottom_color = (
            max(top_color[0] - 40, 0),
            max(top_color[1] - 40, 0),
            max(top_color[2] - 40, 0),
        )
        img = self._create_gradient(width, height, top_color, bottom_color)
        draw = ImageDraw.Draw(img)

        # Emojis
        if spec.emojis:
            emoji_font = self._get_font(
                self._settings.video.fuentes.emoji, 120,
            )
            emojis_text = " ".join(spec.emojis[:3])
            bbox = draw.textbbox((0, 0), emojis_text, font=emoji_font)
            emoji_w = bbox[2] - bbox[0]
            draw.text(
                ((width - emoji_w) // 2, height // 5),
                emojis_text,
                font=emoji_font,
                fill=(255, 255, 255),
            )

        # Texto principal
        title_font = self._get_font(
            self._settings.video.fuentes.principal, 72,
        )
        lines = self._wrap_text(spec.texto_principal, title_font, width - 120)
        y_pos = height // 2 - (len(lines) * 85) // 2

        text_color = self._hex_to_rgb(spec.color_texto)

        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=title_font)
            line_w = bbox[2] - bbox[0]
            x_pos = (width - line_w) // 2
            self._draw_text_with_outline(
                draw, line, x_pos, y_pos, title_font,
                fill=text_color,
                outline_color=(0, 0, 0),
                outline_width=5,
            )
            y_pos += 85

        # Texto secundario
        if spec.texto_secundario:
            sub_font = self._get_font(
                self._settings.video.fuentes.secundaria, 40,
            )
            sub_lines = self._wrap_text(spec.texto_secundario, sub_font, width - 160)
            y_sub = y_pos + 40
            for line in sub_lines:
                bbox = draw.textbbox((0, 0), line, font=sub_font)
                line_w = bbox[2] - bbox[0]
                x_pos = (width - line_w) // 2
                self._draw_text_with_outline(
                    draw, line, x_pos, y_sub, sub_font,
                    fill=text_color,
                    outline_color=(0, 0, 0),
                    outline_width=3,
                )
                y_sub += 55

        img.save(str(output_path), "PNG", quality=95)
        logger.info("Miniatura generada desde spec: %s", output_path)
        return output_path
