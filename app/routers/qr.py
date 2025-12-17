from __future__ import annotations

import io
import os
import re
from enum import Enum
from typing import Tuple

import qrcode
from fastapi import APIRouter, Body, Depends, HTTPException, Query, Security, status
from fastapi.responses import Response
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field, ConfigDict
from qrcode.constants import ERROR_CORRECT_H, ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q
from qrcode.image.pil import PilImage
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.colormasks import QRColorMask, SolidFillColorMask
from qrcode.image.styles.moduledrawers import CircleModuleDrawer, SquareModuleDrawer
from qrcode.image.svg import SvgImage

# Drawers de módulos adicionales (qrcode>=7; si faltan, degradamos solo esos estilos).
try:
    from qrcode.image.styles.moduledrawers import (
        GappedSquareModuleDrawer,
        RoundedModuleDrawer,
        VerticalBarsDrawer,
        HorizontalBarsDrawer,
    )
except ImportError:
    GappedSquareModuleDrawer = RoundedModuleDrawer = VerticalBarsDrawer = HorizontalBarsDrawer = None

# Ojos (no están presentes en todas las versiones de qrcode; degradamos a equivalentes locales).
try:
    from qrcode.image.styles.eyedrawers import CircleEyeDrawer, RoundedEyeDrawer, SquareEyeDrawer
except ImportError:
    from PIL import Image, ImageDraw
    from qrcode.image.styles.moduledrawers.pil import StyledPilQRModuleDrawer

    AA_FACTOR = 4  # antialiasing

    class SquareEyeDrawer(StyledPilQRModuleDrawer):  # type: ignore[misc]
        needs_neighbors = False

        def initialize(self, *args, **kwargs):
            super().initialize(*args, **kwargs)
            self._draw = ImageDraw.Draw(self.img._img)

        def drawrect(self, box, is_active: bool):
            if is_active:
                self._draw.rectangle(box, fill=self.img.paint_color)

    class CircleEyeDrawer(StyledPilQRModuleDrawer):  # type: ignore[misc]
        needs_neighbors = False

        def initialize(self, *args, **kwargs):
            super().initialize(*args, **kwargs)
            size = self.img.box_size
            big = size * AA_FACTOR
            circle = Image.new(self.img.mode, (big, big), self.img.color_mask.back_color)
            ImageDraw.Draw(circle).ellipse((0, 0, big, big), fill=self.img.paint_color)
            self.circle = circle.resize((size, size), Image.Resampling.LANCZOS)

        def drawrect(self, box, is_active: bool):
            if is_active:
                self.img._img.paste(self.circle, (box[0][0], box[0][1]))

    class RoundedEyeDrawer(StyledPilQRModuleDrawer):  # type: ignore[misc]
        needs_neighbors = False

        def __init__(self, radius_ratio: float = 0.25, padding_ratio: float = 0.12):
            self.radius_ratio = radius_ratio
            self.padding_ratio = padding_ratio

        def initialize(self, *args, **kwargs):
            super().initialize(*args, **kwargs)
            size = self.img.box_size
            big = size * AA_FACTOR
            pad = int(big * self.padding_ratio)
            radius = int(big * self.radius_ratio)
            rounded = Image.new(self.img.mode, (big, big), self.img.color_mask.back_color)
            ImageDraw.Draw(rounded).rounded_rectangle(
                (pad, pad, big - pad, big - pad),
                radius=radius,
                fill=self.img.paint_color,
            )
            self.rounded = rounded.resize((size, size), Image.Resampling.LANCZOS)

        def drawrect(self, box, is_active: bool):
            if is_active:
                self.img._img.paste(self.rounded, (box[0][0], box[0][1]))


class OutputFormat(str, Enum):
    png = "png"
    svg = "svg"


class ErrorCorrection(str, Enum):
    L = "L"
    M = "M"
    Q = "Q"
    H = "H"


class Style(str, Enum):
    square = "square"
    dots = "dots"
    rounded = "rounded"
    gapped = "gapped"
    bars_vertical = "bars-vertical"
    bars_horizontal = "bars-horizontal"


class EyeStyle(str, Enum):
    auto = "auto"
    square = "square"
    rounded = "rounded"
    dots = "dots"
    gapped = "gapped"
    bars_vertical = "bars-vertical"
    bars_horizontal = "bars-horizontal"


class FillMode(str, Enum):
    solid = "solid"
    gradient = "gradient"


api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False, description="Clave API si el backend la exige")


class QRRequest(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "examples": [
                {
                    "summary": "PNG solido",
                    "value": {
                        "data": "Hola mundo",
                        "format": "png",
                        "error_correction": "M",
                        "box_size": 10,
                        "border": 4,
                        "fill_color": "#7c3aed",
                        "back_color": "#0b0f1a",
                        "style": "gapped",
                        "eye_style": "square",
                        "eye_color": "#38bdf8",
                        "fill_mode": "solid",
                    },
                },
                {
                    "summary": "PNG degradado y ojos separados",
                    "value": {
                        "data": "https://ejemplo.com",
                        "format": "png",
                        "error_correction": "H",
                        "box_size": 12,
                        "border": 4,
                        "fill_color": "#0ea5e9",
                        "fill_color_to": "#7c3aed",
                        "back_color": "#0f172a",
                        "style": "bars-horizontal",
                        "eye_style": "gapped",
                        "eye_color": "#38bdf8",
                        "fill_mode": "gradient",
                    },
                },
                {
                    "summary": "SVG simple",
                    "value": {
                        "data": "Texto en SVG",
                        "format": "svg",
                        "error_correction": "M",
                        "box_size": 10,
                        "border": 4,
                        "fill_color": "#000000",
                        "back_color": "#ffffff",
                        "style": "square",
                        "eye_style": "auto",
                        "fill_mode": "solid"
                    },
                },
            ]
        },
    )
    data: str = Field(..., min_length=1, max_length=1024, description="Texto o URL a codificar")
    output_format: OutputFormat = Field(default=OutputFormat.png, alias="format")
    error_correction: ErrorCorrection = Field(default=ErrorCorrection.M)
    box_size: int = Field(default=10, ge=1, le=32)
    border: int = Field(default=4, ge=0, le=10)
    fill_color: str = Field(default="#7c3aed")
    fill_mode: FillMode = Field(default=FillMode.solid)
    fill_color_to: str | None = Field(default=None)
    back_color: str = Field(default="#0b0f1a")
    eye_color: str | None = Field(default="#38bdf8")
    eye_style: EyeStyle = Field(default=EyeStyle.square)
    style: Style = Field(default=Style.gapped)


def require_api_key(x_api_key: str | None = Security(api_key_header)) -> str | None:
    expected = os.getenv("QR_API_KEY")
    if expected and x_api_key != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key incorrecta o no proporcionada")
    return x_api_key


router = APIRouter(tags=["qr"], dependencies=[Depends(require_api_key)])


def _validate_color(value: str, param_name: str) -> str:
    match = re.fullmatch(r"#?(?P<hex>[0-9a-fA-F]{6}|[0-9a-fA-F]{3})", value)
    if not match:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Color inválido para '{param_name}'. Usa hex como #ff0000 o #f00.",
        )
    hex_value = match.group("hex")
    if len(hex_value) == 3:
        hex_value = "".join(ch * 2 for ch in hex_value)
    return f"#{hex_value.lower()}"


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    hex_digits = hex_color.lstrip("#")
    return tuple(int(hex_digits[i : i + 2], 16) for i in (0, 2, 4))


def _make_linear_gradient(size: tuple[int, int], start: tuple[int, int, int], end: tuple[int, int, int]):
    """Crea un degradado vertical simple del color start al end."""
    from PIL import Image

    width, height = size
    gradient = Image.new("RGBA", (width, height), (*start, 255))
    if height <= 1:
        return gradient
    pixels = gradient.load()
    for y in range(height):
        t = y / (height - 1)
        color = tuple(int(start[i] * (1 - t) + end[i] * t) for i in range(3)) + (255,)
        for x in range(width):
            pixels[x, y] = color
    return gradient


class EyeColorMask(SolidFillColorMask):
    """Color mask que permite color distinto para los ojos del QR."""

    def __init__(self, back_color, front_color, eye_color):
        super().__init__(back_color=back_color, front_color=front_color)
        self.eye_color = eye_color
        self._img = None

    def initialize(self, styledPilImage, image):
        self._img = styledPilImage
        super().initialize(styledPilImage, image)

    def get_fg_pixel(self, image, x, y):
        if not self._img:
            return self.front_color
        # Mapear pixel a fila/columna de módulo
        row = (y // self._img.box_size) - self._img.border
        col = (x // self._img.box_size) - self._img.border
        if 0 <= row < self._img.width and 0 <= col < self._img.width and self._img.is_eye(row, col):
            return self.eye_color
        return self.front_color

    def apply_mask(self, image):
        QRColorMask.apply_mask(self, image, use_cache=False)


class EyeGradientMask(QRColorMask):
    """Aplica degradado al cuerpo y color fijo a los ojos."""

    def __init__(self, back_color, front_from, front_to, eye_color):
        self.back_color = back_color
        self.front_from = front_from
        self.front_to = front_to
        self.eye_color = eye_color
        self._img = None
        self.height = 1
        self.has_transparency = len(back_color) == 4

    def initialize(self, styledPilImage, image):
        self._img = styledPilImage
        self.height = styledPilImage.pixel_size
        super().initialize(styledPilImage, image)

    def _interp(self, t: float) -> tuple[int, int, int]:
        return tuple(int(self.front_from[i] * (1 - t) + self.front_to[i] * t) for i in range(3))

    def get_fg_pixel(self, image, x, y):
        if not self._img:
            return self.front_from
        row = (y // self._img.box_size) - self._img.border
        col = (x // self._img.box_size) - self._img.border
        if 0 <= row < self._img.width and 0 <= col < self._img.width and self._img.is_eye(row, col):
            return self.eye_color
        t = min(max(y / max(self.height - 1, 1), 0), 1)
        return self._interp(t)

    def apply_mask(self, image):
        QRColorMask.apply_mask(self, image, use_cache=False)


def _require_or_none(cls):
    return cls() if cls else None


def _get_drawers(style: Style, eye_style: EyeStyle) -> Tuple[object | None, object | None]:
    if style == Style.square:
        module = None
    elif style == Style.dots:
        module = _require_or_none(CircleModuleDrawer)
    elif style == Style.rounded:
        module = _require_or_none(RoundedModuleDrawer)
    elif style == Style.gapped:
        module = _require_or_none(GappedSquareModuleDrawer)
    elif style == Style.bars_vertical:
        module = _require_or_none(VerticalBarsDrawer)
    elif style == Style.bars_horizontal:
        module = _require_or_none(HorizontalBarsDrawer)
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Estilo '{style}' no soportado")

    if eye_style == EyeStyle.square:
        eye = _require_or_none(SquareEyeDrawer)
    elif eye_style == EyeStyle.rounded:
        eye = _require_or_none(RoundedEyeDrawer)
    elif eye_style == EyeStyle.dots:
        eye = _require_or_none(CircleModuleDrawer)
    elif eye_style == EyeStyle.gapped:
        eye = _require_or_none(GappedSquareModuleDrawer)
    elif eye_style == EyeStyle.bars_vertical:
        eye = _require_or_none(VerticalBarsDrawer)
    elif eye_style == EyeStyle.bars_horizontal:
        eye = _require_or_none(HorizontalBarsDrawer)
    else:  # auto
        if style == Style.dots:
            eye = _require_or_none(CircleModuleDrawer)
        elif style == Style.rounded:
            eye = _require_or_none(RoundedEyeDrawer)
        elif style == Style.gapped:
            eye = _require_or_none(GappedSquareModuleDrawer)
        elif style == Style.bars_vertical:
            eye = _require_or_none(VerticalBarsDrawer)
        elif style == Style.bars_horizontal:
            eye = _require_or_none(HorizontalBarsDrawer)
        else:
            eye = _require_or_none(SquareEyeDrawer)

    return module, eye


def _generate_qr_response(
    *,
    data: str,
    output_format: OutputFormat,
    error_correction: ErrorCorrection,
    box_size: int,
    border: int,
    fill_color: str,
    back_color: str,
    eye_color: str | None,
    eye_style: EyeStyle,
    style: Style,
    fill_mode: FillMode,
    fill_color_to: str | None,
) -> Response:
    # Forzar restricciones de SVG: sin estilos ni colores custom de ojos/degradado.
    if output_format == OutputFormat.svg:
        style = Style.square
        eye_style = EyeStyle.auto
        eye_color = None
        fill_mode = FillMode.solid
        fill_color_to = None

    error_map = {
        ErrorCorrection.L: ERROR_CORRECT_L,
        ErrorCorrection.M: ERROR_CORRECT_M,
        ErrorCorrection.Q: ERROR_CORRECT_Q,
        ErrorCorrection.H: ERROR_CORRECT_H,
    }

    fill = _validate_color(fill_color, "fill_color") if fill_color else "#000000"
    back = _validate_color(back_color, "back_color") if back_color else "#ffffff"
    fill_to = _validate_color(fill_color_to, "fill_color_to") if fill_color_to else fill
    eye = _validate_color(eye_color, "eye_color") if eye_color else fill
    fill_rgb = _hex_to_rgb(fill)
    fill_to_rgb = _hex_to_rgb(fill_to)
    back_rgb = _hex_to_rgb(back)
    eye_rgb = _hex_to_rgb(eye)

    qr = qrcode.QRCode(
        version=None,
        error_correction=error_map[error_correction],
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)

    if output_format == OutputFormat.svg:
        if style != Style.square or eye_style != EyeStyle.auto or eye_color or fill_mode != FillMode.solid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Los estilos personalizados (estilo/ojos/degradado) solo aplican a PNG",
            )
        img = qr.make_image(image_factory=SvgImage, fill_color=fill, back_color=back)
        out = io.BytesIO()
        img.save(out)
        return Response(
            content=out.getvalue(),
            media_type="image/svg+xml",
            headers={"Content-Disposition": 'inline; filename=\"qr.svg\"'},
        )

    module_drawer, eye_drawer = _get_drawers(style, eye_style)

    if not module_drawer and (eye_color or eye_style != EyeStyle.auto):
        module_drawer = _require_or_none(SquareModuleDrawer)
        eye_drawer = eye_drawer or _require_or_none(SquareEyeDrawer)

    if fill_mode == FillMode.gradient and fill_rgb != fill_to_rgb:
        color_mask: QRColorMask = EyeGradientMask(
            back_color=back_rgb, front_from=fill_rgb, front_to=fill_to_rgb, eye_color=eye_rgb
        )
    else:
        color_mask = (
            EyeColorMask(back_color=back_rgb, front_color=fill_rgb, eye_color=eye_rgb)
            if eye_rgb != fill_rgb
            else SolidFillColorMask(front_color=fill_rgb, back_color=back_rgb)
        )

    if module_drawer:
        img = qr.make_image(
            image_factory=StyledPilImage,
            module_drawer=module_drawer,
            eye_drawer=eye_drawer,
            color_mask=color_mask,
        )
    else:
        img = qr.make_image(image_factory=PilImage, fill_color=fill_rgb, back_color=back_rgb)

    out = io.BytesIO()
    img.save(out, format="PNG")
    return Response(
        content=out.getvalue(),
        media_type="image/png",
        headers={"Content-Disposition": 'inline; filename=\"qr.png\"'},
    )


@router.post(
    "/qr",
    summary="Generar QR (JSON body)",
    description=(
        "Genera un QR en PNG o SVG. Los estilos personalizados (estilo de cuerpo, ojos y degradado) "
        "solo se aplican en PNG; en SVG se fuerza estilo cuadrado, ojos automáticos y color sólido."
    ),
    response_description="Imagen QR en PNG o SVG",
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "examples": {
                        "png_solid": {
                            "summary": "Ejemplo PNG solido",
                            "value": {
                                "data": "Hola mundo",
                                "format": "png",
                                "error_correction": "M",
                                "box_size": 10,
                                "border": 4,
                                "fill_color": "#7c3aed",
                                "back_color": "#0b0f1a",
                                "style": "gapped",
                                "eye_style": "square",
                                "eye_color": "#38bdf8",
                                "fill_mode": "solid",
                            },
                        },
                        "png_gradient": {
                            "summary": "Ejemplo PNG degradado",
                            "value": {
                                "data": "https://ejemplo.com",
                                "format": "png",
                                "error_correction": "H",
                                "box_size": 12,
                                "border": 4,
                                "fill_color": "#0ea5e9",
                                "fill_color_to": "#7c3aed",
                                "back_color": "#0f172a",
                                "style": "bars-horizontal",
                                "eye_style": "gapped",
                                "eye_color": "#38bdf8",
                                "fill_mode": "gradient",
                            },
                        },
                        "svg_simple": {
                            "summary": "Ejemplo SVG simple",
                            "value": {
                                "data": "Texto en SVG",
                                "format": "svg",
                                "error_correction": "M",
                                "box_size": 10,
                                "border": 4,
                                "fill_color": "#000000",
                                "back_color": "#ffffff",
                                "style": "square",
                                "eye_style": "auto",
                                "fill_mode": "solid"
                            },
                        },
                    }
                }
            }
        }
    },
)
def generate_qr_body(payload: QRRequest = Body(...)) -> Response:
    return _generate_qr_response(
        data=payload.data,
        output_format=payload.output_format,
        error_correction=payload.error_correction,
        box_size=payload.box_size,
        border=payload.border,
        fill_color=payload.fill_color,
        back_color=payload.back_color,
        eye_color=payload.eye_color,
        eye_style=payload.eye_style,
        style=payload.style,
        fill_mode=payload.fill_mode,
        fill_color_to=payload.fill_color_to,
    )
