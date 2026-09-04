from pathlib import Path

try:
    import cairosvg
except ImportError as exc:
    raise SystemExit(
        "CairoSVG is required but not installed.\n"
        "Install it with:\n"
        "  pip install cairosvg\n"
        "or your distro's package manager (e.g. sudo pacman -S python-cairosvg)."
    ) from exc


def convert_svg_to_png(input_svg_path, output_png_path, width=256):
    """Converts a local SVG file into a PNG image, width pixels wide."""
    output_png_path = Path(output_png_path)

    # if our png exists already, rename it to <stem>_001.png, or _002 etc.
    if output_png_path.is_file():
        increment = 1
        while True:
            candidate = output_png_path.with_name(
                f"{output_png_path.stem}_old_{increment:03d}{output_png_path.suffix}"
            )
            if not candidate.is_file():
                output_png_path.rename(candidate)
                print(f"Existing file renamed to {candidate}")
                break
            increment += 1

    try:
        cairosvg.svg2png(url=str(input_svg_path), write_to=str(output_png_path), output_width=width)
        print(f"Successfully converted {input_svg_path} -> {output_png_path}")
    except Exception as e:
        print(f"Error converting file: {e}")

if __name__ == "__main__":
    script_dir = Path(__file__).parent.resolve()
    input_svg_path  = script_dir / "folder.svg"
    output_png_path = script_dir / "folder.png"

    # Let's convert
    convert_svg_to_png(input_svg_path, output_png_path)
