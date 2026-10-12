def calculate_dimension(expression: str) -> tuple[str, str | None]:
    """
    Mengecek apakah input berupa rumus dimensi (misal: '2x3x4' atau '2.5 * 4').
    Mengembalikan tuple: (Hasil_Kalkulasi, Rumus_Asli_Jika_Ada)
    """
    # Bersihkan spasi dan ubah 'x' atau 'X' menjadi '*' untuk kalkulasi
    clean_expr = expression.lower().replace(" ", "").replace("x", "*")

    if "*" in clean_expr:
        try:
            parts = clean_expr.split("*")
            total = 1.0
            for p in parts:
                total *= float(p)

            # Hilangkan desimal (.0) jika hasilnya adalah bilangan bulat utuh
            result_str = str(int(total)) if total.is_integer() else str(round(total, 4))

            # Kembalikan: ("24", "2 x 3 x 4")
            return result_str, expression.strip()
        except ValueError:
            # Jika gagal (misal salah ketik "2x3xA"), kembalikan teks aslinya
            return expression.strip(), None

    # Jika angka biasa (misal "10"), langsung kembalikan aslinya
    return expression.strip(), None