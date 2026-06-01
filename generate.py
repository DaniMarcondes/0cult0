#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════╗
║        PORTAL SAGRADO — Gerador de Grimório Digital      ║
║        Execute este script na pasta do seu drive.        ║
║        Ele varre todos os .html e regenera o index.      ║
╚══════════════════════════════════════════════════════════╝

USO:
  python generate.py

REQUISITOS:
  Python 3.6+ (sem dependências externas — usa só stdlib)

COMO A DIVISÃO FUNCIONA AGORA (por PASTAS):
  • Cada PASTA de primeiro nível dentro desta pasta vira uma SEÇÃO do índice.
        01_ORACULOS/            → seção "Tarô, Oráculos & Sistemas Divinatórios"
        08_GNOSTICISMO/         → seção "Gnosticismo, Apócrifos & Mística Cristã"
  • SUBPASTAS viram SUBGRUPOS dentro da seção (com rótulo próprio).
        08_GNOSTICISMO/ESTUDO APOCRIFO (CLARO)/  → subgrupo "Estudo Apócrifo (Claro)"
        06_.../METAFISICA/DESIGN NOVO/           → subgrupo "Metafísica · Design Novo"
  • TODO arquivo .html vira um botão — TENHA ELE PREFIXO NUMÉRICO OU NÃO.
        Basta jogar um arquivo .html novo dentro de qualquer pasta e rodar
        este script: um botão novo aparece automaticamente para ele.
  • A ordem das seções segue o prefixo numérico do nome da pasta (01, 02, 04…);
    pastas sem número vão para o fim, em ordem alfabética.

PARA CRIAR/RENOMEAR UMA SEÇÃO:
  • Renomeie a pasta no disco (o nome da pasta já define a seção), OU
  • Adicione/edite uma entrada em SECTION_MAP abaixo para um título mais bonito.
"""

import os
import re
import html
from pathlib import Path
from datetime import datetime

# ── Configurações ──────────────────────────────────────────
SCRIPT_DIR   = Path(__file__).parent.resolve()   # pasta onde o script está
INDEX_FILE   = SCRIPT_DIR / "index.html"          # arquivo de saída
IGNORE_FILES = {"index.html"}                     # arquivos a ignorar

# ── Mapa de SEÇÕES pelo NÚMERO da pasta ────────────────────
# Chave  : número do prefixo da pasta de primeiro nível (01 → 1, 10 → 10)
# Valor  : (título bonito exibido, ícone/sigilo da seção)
#
# Usamos o NÚMERO (e não o nome inteiro) como chave de propósito: assim o
# título certo aparece mesmo que o nome da pasta tenha acento, espaço ou
# algum caractere estranho herdado de zip/sistema antigo.
# Pastas sem número (ou número não listado) recebem um título derivado
# automaticamente do próprio nome.
SECTION_MAP: dict[int, tuple[str, str]] = {
    1:  ("Tarô, Oráculos & Sistemas Divinatórios",       "🃏"),
    2:  ("Ocultismo, Magia & Hermetismo",                "🕯"),
    3:  ("Cabala & Árvore da Vida",                      "✡"),
    4:  ("Astrologia",                                   "♑"),
    5:  ("Energia, Chakras & Meditação",                 "✦"),
    6:  ("Projeção, Metafísica & Cosmologia",            "💫"),
    7:  ("Religiões, Mitologias & Civilizações Antigas", "☸"),
    8:  ("Gnosticismo, Apócrifos & Mística Cristã",      "👁"),
    9:  ("Ufologia, ETs & Cosmologias Alternativas",     "🌙"),
    10: ("Estudos Gerais & Materiais Mistos",            "📜"),
}

# Sigilos por palavra-chave no nome do arquivo (tem prioridade sobre o ícone da seção)
ICON_MAP = {
    "tarot": "🃏", "taro": "🃏", "arcano": "🃏", "carta": "🃏", "baralho": "🃏",
    "astro": "♑", "signo": "♑", "mapa": "🗺", "natal": "♑", "astral": "♑",
    "alquimia": "⚗", "alquimic": "⚗", "opus": "⚗",
    "ritual": "🕯", "trabalho": "🕯", "evocac": "🕯", "invocac": "🕯", "magia": "✦", "feitico": "✦",
    "lua": "🌙", "lunar": "🌙", "ufo": "🛸", "raca": "🛸", "et": "🛸", "extraterr": "🛸",
    "cabala": "✡", "kabala": "✡", "sephirot": "✡", "sefer": "✡", "yetzirah": "✡",
    "hermet": "☿", "hermes": "☿", "agrippa": "☿",
    "anjo": "👁", "enoch": "👁", "olho": "👁",
    "chakra": "🌀", "kundalini": "🐍", "meditac": "🧘", "violao": "🎼", "violino": "🎼",
    "sexual": "🜍", "sexo": "🜍",
    "geometria": "🔷", "sagrada": "🔷",
    "cosmo": "🌌", "metafisic": "🌌", "conciencia": "🌌", "consciencia": "🌌", "inteligencia": "🌌",
    "projecao": "💫", "vale": "💫",
    "egip": "☥", "egipci": "☥", "morto": "☥",
    "grega": "⚡", "hindu": "🕉", "mito": "☸",
    "genesis": "👁", "sophia": "👁", "phisis": "👁", "madalena": "👁", "apocrifo": "📖", "apocalip": "📖",
    "lovecraft": "🐙", "mentira": "🃏",
    "simbolo": "✶", "sigil": "✶", "grimor": "✦",
}
DEFAULT_ICON = "📜"

# Acentuação/grafia bonita para palavras que no disco vêm sem acento
TITLE_FIXES = {
    "Racas": "Raças", "Raca": "Raça",
    "Conciencia": "Consciência", "Consciencia": "Consciência",
    "Metafisica": "Metafísica", "Metafisica1": "Metafísica 1",
    "Apocrifo": "Apócrifo", "Apocrifa": "Apócrifa",
    "Simbolos": "Símbolos", "Simbolo": "Símbolo",
    "Genesis": "Gênesis", "Egipcio": "Egípcio", "Egipcia": "Egípcia",
    "Mitologico": "Mitológico", "Mitologica": "Mitológica",
    "Exercicios": "Exercícios", "Esoterico": "Esotérico", "Esoterica": "Esotérica",
    "Inteligencias": "Inteligências", "Projecao": "Projeção",
    "Violao": "Violão", "Cigano": "Cigano", "Hinduismo": "Hinduísmo",
    "Estranheza": "Estranheza", "Conciencia-": "Consciência ",
    "Phisis": "Phisis", "Sophia": "Sophia",
}

# ── Regex do prefixo numérico (usado só p/ limpar título e ordenar pastas) ──
_PREFIX_RE = re.compile(r'^(\d+)(\.[0-9]+|[A-Z])?[_-]', re.IGNORECASE)
_FOLDER_NUM_RE = re.compile(r'^(\d+)')


# ── Funções de utilidade ───────────────────────────────────

def apply_fixes(text: str) -> str:
    """Aplica acentuação bonita palavra a palavra."""
    out = []
    for w in text.split():
        out.append(TITLE_FIXES.get(w, w))
    return " ".join(out)


def clean_title(filename: str) -> str:
    """
    Remove o prefixo numérico (se houver) e devolve um título legível.
      "05_kundalini-completa.html" → "Kundalini Completa"
      "cosmo-parte1.html"          → "Cosmo Parte1"   (sem prefixo: usa o nome todo)
      "09_Racas-vol1.html"         → "Raças Vol1"
    """
    stem = Path(filename).stem
    title = _PREFIX_RE.sub('', stem, count=1)   # tira "NN_" se existir
    title = re.sub(r'[-_]+', ' ', title).strip()
    title = title.title()
    return apply_fixes(title)


def clean_folder_label(name: str) -> str:
    """Rótulo bonito para subpastas: 'DESIGN NOVO' → 'Design Novo'."""
    label = _PREFIX_RE.sub('', name, count=1)
    label = re.sub(r'[_]+', ' ', label).strip()
    label = label.title()
    return apply_fixes(label)


def section_info(folder_name: str) -> tuple[str, str]:
    """Título e ícone da seção a partir do nome da pasta de 1º nível.
    Procura pelo NÚMERO do prefixo; se não houver mapa, deriva do nome."""
    m = _FOLDER_NUM_RE.match(folder_name)
    if m:
        num = int(m.group(1))
        if num in SECTION_MAP:
            return SECTION_MAP[num]
    return (clean_folder_label(folder_name), DEFAULT_ICON)


def folder_sort_key(folder_name: str) -> tuple[int, str]:
    """Ordena pastas pelo número do prefixo; sem número vai pro fim."""
    m = _FOLDER_NUM_RE.match(folder_name)
    num = int(m.group(1)) if m else 9999
    return (num, folder_name.lower())


def get_icon(name: str, fallback: str) -> str:
    """Ícone pelo nome do arquivo; cai no ícone da seção."""
    n = name.lower()
    for kw, icon in ICON_MAP.items():
        if kw in n:
            return icon
    return fallback


def natural_key(s: str):
    """Ordenação natural: Parte1, Parte2, … Parte10 (não Parte1, Parte10, Parte2)."""
    return [int(t) if t.isdigit() else t.lower()
            for t in re.split(r'(\d+)', s)]


def relative_path(p: Path) -> str:
    """Caminho relativo ao index.html (na raiz da pasta)."""
    return str(p.relative_to(SCRIPT_DIR)).replace('\\', '/')


# ── Coleta dos arquivos ────────────────────────────────────

def collect() -> dict[str, dict[str, list[Path]]]:
    """
    Varre tudo e devolve uma estrutura:
        { pasta_topo : { subcaminho_relativo : [arquivos .html] } }
    onde subcaminho_relativo == "" significa "direto na raiz da seção".
    Arquivos .html soltos na raiz da pasta vão para a seção "10_GERAL".
    """
    tree: dict[str, dict[str, list[Path]]] = {}

    for root, dirs, files in os.walk(SCRIPT_DIR):
        dirs[:] = [d for d in dirs if not d.startswith('.')]   # ignora .git etc.
        root_path = Path(root)
        for f in files:
            if not f.lower().endswith('.html'):
                continue
            if f.lower() in IGNORE_FILES:
                continue

            p = root_path / f
            rel_parts = p.relative_to(SCRIPT_DIR).parts   # ex: ('06_...', 'METAFISICA', 'DESIGN NOVO', 'x.html')

            if len(rel_parts) == 1:
                # arquivo solto na raiz → manda pra seção Geral
                top = "10_GERAL"
                sub = ""
            else:
                top = rel_parts[0]
                sub = "/".join(rel_parts[1:-1])   # subpastas entre a seção e o arquivo

            tree.setdefault(top, {}).setdefault(sub, []).append(p)

    return tree


# ── Montagem do HTML ───────────────────────────────────────

def build_button(p: Path, section_icon: str) -> str:
    title    = clean_title(p.name)
    path     = relative_path(p)
    icon     = get_icon(p.name, section_icon)
    esc_name = html.escape(title)
    esc_path = html.escape(path)
    # data-search reúne nome + caminho (sem acento o JS normaliza) p/ a busca
    esc_search = html.escape(f"{title} {path}".lower())
    return (
        f'        <a class="scroll-link" href="{esc_path}" title="{esc_name}" data-search="{esc_search}">\n'
        f'          <span class="scroll-icon">{icon}</span>\n'
        f'          <span class="scroll-name">{esc_name}</span>\n'
        f'          <span class="scroll-corner">✦</span>\n'
        f'          <span class="scroll-path">{esc_path}</span>\n'
        f'        </a>'
    )


def build_grid(files: list[Path], section_icon: str) -> str:
    files_sorted = sorted(files, key=lambda p: natural_key(p.stem))
    btns = [build_button(p, section_icon) for p in files_sorted]
    return '      <div class="grimoire-grid">\n' + '\n'.join(btns) + '\n      </div>'


def build_section(folder_name: str, subs: dict[str, list[Path]]) -> tuple[str, int]:
    title, icon = section_info(folder_name)
    total = sum(len(v) for v in subs.values())

    parts = []
    parts.append('    <section class="section-block fade-in">')
    parts.append(
        f'      <h2 class="section-title">'
        f'<span class="section-icon">{icon}</span>'
        f'<span class="section-label">{html.escape(title)}</span>'
        f'<span class="section-count">{total}</span></h2>'
    )

    # 1) arquivos direto na raiz da seção (sub == "")
    if "" in subs and subs[""]:
        parts.append(build_grid(subs[""], icon))

    # 2) subgrupos (subpastas), em ordem alfabética/natural pelo caminho
    for sub in sorted([s for s in subs if s], key=natural_key):
        label = " · ".join(clean_folder_label(seg) for seg in sub.split("/"))
        parts.append('      <div class="subgroup">')
        parts.append(f'        <h3 class="subgroup-title">{html.escape(label)}</h3>')
        parts.append(build_grid(subs[sub], icon))
        parts.append('      </div>')

    parts.append('    </section>')
    return ('\n'.join(parts), total)


def build_content(tree: dict[str, dict[str, list[Path]]]) -> tuple[str, int]:
    if not tree:
        empty = (
            '    <section class="section-block">\n'
            '      <div class="grimoire-grid">\n'
            '        <div class="empty-state">\n'
            '          <span class="empty-icon">📜</span>\n'
            '          Nenhum arquivo encontrado ainda.<br>\n'
            '          Crie pastas (ex.: <em>01_ORACULOS</em>) e jogue arquivos <em>.html</em> dentro, depois execute novamente.\n'
            '        </div>\n'
            '      </div>\n'
            '    </section>'
        )
        return (empty, 0)

    sections = []
    grand_total = 0
    for folder in sorted(tree.keys(), key=folder_sort_key):
        section_html, n = build_section(folder, tree[folder])
        sections.append(section_html)
        grand_total += n

    return ('\n'.join(sections), grand_total)


def inject_content(template_html: str, content: str, file_count: int) -> str:
    """Injeta o conteúdo entre os marcadores no HTML."""
    now = datetime.now().strftime('%d/%m/%Y %H:%M')
    plural = 's' if file_count != 1 else ''

    header = (
        f'    <!-- Gerado automaticamente por generate.py em {now} | {file_count} arquivo(s) -->\n'
        f'    <p class="portal-intro fade-in" style="text-align:center; margin:0 auto 2.4rem; animation-delay:0.2s">\n'
        f'      <span style="font-family:\'Space Mono\',monospace; font-size:0.74rem; letter-spacing:0.28em; '
        f'text-transform:uppercase; color:var(--lime); text-shadow:0 0 14px rgba(57,255,20,0.4);">\n'
        f'        ✦ {file_count} pergaminho{plural} no acervo ✦\n'
        f'      </span>\n'
        f'    </p>\n'
    )
    new_content = f'\n{header}\n{content}\n    '

    pattern = r'(<!-- INÍCIO DOS ARQUIVOS[^>]*-->).*?(<!-- FIM DOS ARQUIVOS[^>]*-->)'
    result = re.sub(pattern, lambda m: f'{m.group(1)}{new_content}{m.group(2)}',
                    template_html, flags=re.DOTALL)
    return result


# ── Ponto de entrada ───────────────────────────────────────

def main():
    print("━" * 56)
    print("  ✦  Portal Sagrado — Gerador de Grimório Digital  ✦")
    print("━" * 56)

    if not INDEX_FILE.exists():
        print(f"\n⚠  index.html não encontrado em: {SCRIPT_DIR}")
        print("   Coloque index.html e generate.py na mesma pasta.\n")
        return

    tree = collect()

    # Relatório no terminal
    total = 0
    print(f"\n📁 Pasta varrida: {SCRIPT_DIR}\n")
    for folder in sorted(tree.keys(), key=folder_sort_key):
        title, _ = section_info(folder)
        n = sum(len(v) for v in tree[folder].values())
        total += n
        print(f"  ▣ {folder}  →  {title}  [{n}]")
        for sub in sorted([s for s in tree[folder] if s], key=natural_key):
            print(f"      └ {sub}  [{len(tree[folder][sub])}]")
    print(f"\n📜 Total de arquivos .html: {total}")

    content, count = build_content(tree)
    template = INDEX_FILE.read_text(encoding='utf-8')

    # Salvaguarda: se os marcadores sumiram (ou o arquivo está vazio),
    # NÃO regrava — assim nunca zeramos o index por engano.
    if "INÍCIO DOS ARQUIVOS" not in template or "FIM DOS ARQUIVOS" not in template:
        print("\n⚠  Marcadores não encontrados no index.html (ou arquivo vazio).")
        print("   Nada foi alterado. Restaure um index.html que contenha:")
        print("     <!-- INÍCIO DOS ARQUIVOS ... -->")
        print("     <!-- FIM DOS ARQUIVOS ... -->\n")
        return

    result = inject_content(template, content, count)
    INDEX_FILE.write_text(result, encoding='utf-8')

    print(f"\n✅ index.html atualizado com sucesso!")
    print(f"   Abra no navegador: {INDEX_FILE}")
    print("\n" + "━" * 56 + "\n")


if __name__ == "__main__":
    main()
