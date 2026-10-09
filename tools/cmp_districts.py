import os
import struct
import matplotlib.pyplot as plt
import matplotlib.patches as patches


TAMANHO_CABECALHO = 28
TAMANHO_MAPA_BASE = 256 * 256 * 4
TAMANHO_LOCALIZACOES = 3 * 6 * 6
TAMANHO_REGISTO_NAV = 35

"""
For example, in this console output:

N.º   Nome                            SAM  X Min  Y Min  X Max  Y Max
0     Chinatown                         3     22     35     50     60
1     Downtown                          7     60     20     95     55

* N.º — index of the navigation record in the file.
* Nome — district name stored in the record.
*  SAM — sample index associated with the district.
* X Min, Y Min — top-left coordinates.
* X Max, Y Max — bottom-right coordinates, calculated from the origin and dimensions.

Important: SAM is not necessarily a district ID or a GXT text ID. Don't use it to look up district names unless you've confirmed the game's mapping.
"""


def ler_coordenadas_distritos_gta1(caminho_cmp):
    """
    Lê os distritos da secção nav_data de um ficheiro GTA 1 .CMP.

    Formato de cada registo:
        x, y, w, h, sam: 5 bytes
        name: 30 bytes

    Devolve uma lista de dicionários com os dados dos distritos.
    """

    if not os.path.isfile(caminho_cmp):
        raise FileNotFoundError(
            f"Ficheiro não encontrado: {caminho_cmp}"
        )

    with open(caminho_cmp, "rb") as f:
        dados = f.read()

    tamanho_ficheiro = len(dados)

    if tamanho_ficheiro < TAMANHO_CABECALHO:
        raise ValueError("O ficheiro é demasiado pequeno para conter o cabeçalho.")

    # ---------------------------------------------------------
    # 1. Ler o cabeçalho de 28 bytes
    # ---------------------------------------------------------

    versao = struct.unpack_from("<I", dados, 0)[0]
    estilo = dados[4]
    numero_amostras = dados[5]

    reservado = struct.unpack_from("<H", dados, 6)[0]

    route_size = struct.unpack_from("<I", dados, 8)[0]
    object_pos_size = struct.unpack_from("<I", dados, 12)[0]
    column_size = struct.unpack_from("<I", dados, 16)[0]
    block_size = struct.unpack_from("<I", dados, 20)[0]
    nav_data_size = struct.unpack_from("<I", dados, 24)[0]

    print(f"Ficheiro: {caminho_cmp}")
    print(f"Tamanho: {tamanho_ficheiro:,} bytes")
    print(f"Versão: {versao}")
    print(f"Estilo: {estilo}")
    print(f"Número de amostras: {numero_amostras}")

    # ---------------------------------------------------------
    # 2. Calcular o offset da secção nav_data
    #
    # Ordem no ficheiro:
    # cabeçalho, mapa base, colunas, blocos, objetos,
    # rotas, localizações e dados de navegação.
    # ---------------------------------------------------------

    offset_colunas = TAMANHO_CABECALHO + TAMANHO_MAPA_BASE
    offset_blocos = offset_colunas + column_size
    offset_objetos = offset_blocos + block_size
    offset_rotas = offset_objetos + object_pos_size
    offset_localizacoes = offset_rotas + route_size
    offset_nav = offset_localizacoes + TAMANHO_LOCALIZACOES

    fim_nav = offset_nav + nav_data_size

    print(f"Tamanho das colunas: {column_size:,}")
    print(f"Tamanho dos blocos: {block_size:,}")
    print(f"Tamanho dos objetos: {object_pos_size:,}")
    print(f"Tamanho das rotas: {route_size:,}")
    print(f"Tamanho dos dados de navegação: {nav_data_size:,}")
    print(f"Offset nav_data: {offset_nav:,} (0x{offset_nav:X})")

    if fim_nav > tamanho_ficheiro:
        raise ValueError(
            "A secção nav_data ultrapassa o fim do ficheiro. "
            "Confirma a versão do formato e os tamanhos do cabeçalho."
        )

    if nav_data_size == 0:
        print("O ficheiro não contém dados de navegação.")
        return []

    if nav_data_size % TAMANHO_REGISTO_NAV != 0:
        raise ValueError(
            f"nav_data_size ({nav_data_size}) não é múltiplo de "
            f"{TAMANHO_REGISTO_NAV}. O formato ou a versão pode ser diferente."
        )

    # ---------------------------------------------------------
    # 3. Ler os registos de navegação
    # ---------------------------------------------------------

    distritos = []
    numero_registos = nav_data_size // TAMANHO_REGISTO_NAV

    print(f"\nRegistos encontrados: {numero_registos}")
    print(
        f"\n{'N.º':<5} {'Nome':<30} {'SAM':>4} "
        f"{'X Min':>6} {'Y Min':>6} {'X Max':>6} {'Y Max':>6}"
    )
    print("-" * 80)

    for i in range(numero_registos):
        pos = offset_nav + i * TAMANHO_REGISTO_NAV

        x, y, w, h, sam = struct.unpack_from("<5B", dados, pos)

        nome_bytes = dados[pos + 5:pos + 35]
        nome = nome_bytes.split(b"\x00", 1)[0].decode(
            "latin-1", errors="replace"
        ).strip()

        # O formato armazena origem e dimensões, não dois pares
        # de coordenadas mínimo/máximo.
        x_min = x
        y_min = y
        x_max = x + w
        y_max = y + h

        distrito = {
            "indice": i,
            "nome": nome or f"Distrito {i}",
            "x": x,
            "y": y,
            "w": w,
            "h": h,
            "sam": sam,
            "x_min": x_min,
            "y_min": y_min,
            "x_max": x_max,
            "y_max": y_max,
        }

        # Avisar sobre dados fora da grelha, sem alterar
        # silenciosamente as coordenadas originais.
        if x_max > 256 or y_max > 256:
            print(
                f"Aviso: registo {i} ultrapassa a grelha 256x256: "
                f"{nome!r}, ({x_min}, {y_min})-({x_max}, {y_max})"
            )

        distritos.append(distrito)

        print(
            f"{i:<5} {distrito['nome'][:30]:<30} {sam:>4} "
            f"{x_min:>6} {y_min:>6} {x_max:>6} {y_max:>6}"
        )

    return distritos


def renderizar_bboxes_gta1(distritos):
    """Desenha as zonas de navegação extraídas do ficheiro CMP."""

    fig, ax = plt.subplots(figsize=(12, 12))

    ax.set_xlim(0, 256)
    ax.set_ylim(256, 0)
    ax.set_aspect("equal", adjustable="box")

    for distrito in distritos:
        x = distrito["x"]
        y = distrito["y"]
        w = distrito["w"]
        h = distrito["h"]

        retangulo = patches.Rectangle(
            (x, y),
            w,
            h,
            linewidth=1.2,
            edgecolor="red",
            facecolor="red",
            alpha=0.15,
        )
        ax.add_patch(retangulo)

        # Mostrar o nome, ou o índice se o nome estiver vazio.
        etiqueta = distrito["nome"]

        ax.text(
            x + w / 2,
            y + h / 2,
            etiqueta,
            fontsize=7,
            color="darkred",
            ha="center",
            va="center",
            wrap=True,
            bbox={
                "facecolor": "white",
                "alpha": 0.65,
                "edgecolor": "none",
                "pad": 1,
            },
        )

    ax.set_title(
        f"GTA 1 — Distritos de navegação ({len(distritos)} zonas)"
    )
    ax.set_xlabel("Coordenada X (blocos)")
    ax.set_ylabel("Coordenada Y (blocos)")

    ax.set_xticks(range(0, 257, 16))
    ax.set_yticks(range(0, 257, 16))
    ax.grid(True, linestyle="--", alpha=0.35)

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    ficheiro = "NYC.CMP"

    try:
        distritos = ler_coordenadas_distritos_gta1(ficheiro)

        if distritos:
            renderizar_bboxes_gta1(distritos)

    except (OSError, ValueError, struct.error) as erro:
        print(f"Erro ao processar o mapa: {erro}")
