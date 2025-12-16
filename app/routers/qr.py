from __future__ import annotations

import io
import os
import re
from enum import Enum

import qrcode
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from fastapi.responses import Response
from qrcode.constants import ERROR_CORRECT_H, ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q
from qrcode.image.pil import PilImage
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.colormasks import SolidFillColorMask
from qrcode.image.styles.moduledrawers import CircleModuleDrawer
from qrcode.image.svg import SvgImage


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


def require_api_key(x_api_key: str | None = Header(default=None)) -> str | None:
    """Enforce X-API-Key when la variable de entorno QR_API_KEY está definida."""
    expected = os.getenv("QR_API_KEY")
    if expected and x_api_key != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key inválida o ausente")
    return x_api_key


router = APIRouter(tags=["qr"], dependencies=[Depends(require_api_key)])


def _validate_color(value: str, param_name: str) -> str:
    """Normaliza colores hex (3 o 6 dígitos) y valida formato."""
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
    """Convierte '#rrggbb' en tuple RGB."""
    hex_digits = hex_color.lstrip("#")
    return tuple(int(hex_digits[i : i + 2], 16) for i in (0, 2, 4))


@router.get("/qr")
def generate_qr(
    data: str = Query(min_length=1, max_length=1024, description="Texto o URL a codificar"),
    output_format: OutputFormat = Query(default=OutputFormat.png, alias="format", description="Formato de salida"),
    error_correction: ErrorCorrection = Query(
        default=ErrorCorrection.M, description="Nivel de corrección de error (L/M/Q/H)"
    ),
    box_size: int = Query(default=10, ge=1, le=32, description="Tamaño de cada módulo"),
    border: int = Query(default=2, ge=0, le=10, description="Borde (módulos)"),
    fill_color: str = Query(default="black", description="Color del QR (hex, ej: #ff0000)"),
    back_color: str = Query(default="white", description="Color de fondo (hex, ej: #ffffff)"),
    style: Style = Query(default=Style.square, description="Estilo de los módulos (square|dots, dots solo en PNG)"),
) -> Response:
    error_map = {
        ErrorCorrection.L: ERROR_CORRECT_L,
        ErrorCorrection.M: ERROR_CORRECT_M,
        ErrorCorrection.Q: ERROR_CORRECT_Q,
        ErrorCorrection.H: ERROR_CORRECT_H,
    }

    fill = _validate_color(fill_color, "fill_color") if fill_color else "#000000"
    back = _validate_color(back_color, "back_color") if back_color else "#ffffff"
    fill_rgb = _hex_to_rgb(fill)
    back_rgb = _hex_to_rgb(back)

    qr = qrcode.QRCode(
        version=None,
        error_correction=error_map[error_correction],
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)

    if output_format == OutputFormat.svg:
        if style == Style.dots:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El estilo 'dots' solo aplica a PNG")
        img = qr.make_image(image_factory=SvgImage, fill_color=fill, back_color=back)
        out = io.BytesIO()
        img.save(out)
        return Response(
            content=out.getvalue(),
            media_type="image/svg+xml",
            headers={"Content-Disposition": 'inline; filename="qr.svg"'},
        )

    if style == Style.dots:
        img = qr.make_image(
            image_factory=StyledPilImage,
            module_drawer=CircleModuleDrawer(),
            color_mask=SolidFillColorMask(front_color=fill_rgb, back_color=back_rgb),
        )
    else:
        img = qr.make_image(image_factory=PilImage, fill_color=fill_rgb, back_color=back_rgb)

    out = io.BytesIO()
    img.save(out, format="PNG")
    return Response(
        content=out.getvalue(),
        media_type="image/png",
        headers={"Content-Disposition": 'inline; filename="qr.png"'},
    )
