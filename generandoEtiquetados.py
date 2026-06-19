import streamlit as st
import time
import pandas as pd
import io

# ── Solver ────────────────────────────────────────────────────────────────────

def solve(N, x_fixed=None):
    """
    Retorna todas las soluciones para el sistema tridiagonal con valores en {1..4N}.
    x_fixed: dict {pos: valor} con posiciones fijadas de antemano (opcional).
    """
    n2 = 2 * N
    total = 4 * N
    solutions = []

    xs = [0] * n2
    in_available = [True] * (total + 1)
    ys = [None] * n2

    if x_fixed is None:
        x_fixed = {}

    # Validación temprana
    for pos, val in x_fixed.items():
        if not (0 <= pos < n2):
            raise ValueError(f"Posición fija {pos} fuera de rango [0, {n2-1}].")
        if not (1 <= val <= total):
            raise ValueError(f"Valor fijo {val} fuera de rango [1, {total}].")
    if len(set(x_fixed.values())) < len(x_fixed):
        raise ValueError("Hay valores duplicados en x_fixed.")

    def y_at(i):
        if i == 0:
            return 2 * xs[0] - xs[1]
        elif i == n2 - 1:
            return 2 * xs[n2 - 1] - xs[n2 - 2]
        else:
            return 3 * xs[i] - xs[i - 1] - xs[i + 1]

    def try_set_y(i):
        v = y_at(i)
        if v < 1 or v > total:
            return False
        if not in_available[v]:
            return False
        ys[i] = v
        in_available[v] = False
        return True

    def unset_y(i):
        if ys[i] is not None:
            in_available[ys[i]] = True
            ys[i] = None

    def backtrack(pos):
        if pos == n2:
            if try_set_y(n2 - 1):
                solutions.append((list(xs), list(ys)))
                unset_y(n2 - 1)
            return

        if pos in x_fixed:
            v = x_fixed[pos]
            if not in_available[v]:
                return
            xs[pos] = v
            in_available[v] = False
            valid = True
            computed = []
            if pos == 1:
                if try_set_y(0):
                    computed.append(0)
                else:
                    valid = False
            if valid and pos >= 2 and pos < n2 - 1:
                if try_set_y(pos - 1):
                    computed.append(pos - 1)
                else:
                    valid = False
            if valid and pos == n2 - 1 and n2 >= 3:
                if try_set_y(n2 - 2):
                    computed.append(n2 - 2)
                else:
                    valid = False
            if valid:
                backtrack(pos + 1)
            for i in computed:
                unset_y(i)
            in_available[v] = True
            xs[pos] = 0
        else:
            for v in range(1, total + 1):
                if not in_available[v]:
                    continue
                xs[pos] = v
                in_available[v] = False
                valid = True
                computed = []
                if pos == 1:
                    if try_set_y(0):
                        computed.append(0)
                    else:
                        valid = False
                if valid and pos >= 2 and pos < n2 - 1:
                    if try_set_y(pos - 1):
                        computed.append(pos - 1)
                    else:
                        valid = False
                if valid and pos == n2 - 1 and n2 >= 3:
                    if try_set_y(n2 - 2):
                        computed.append(n2 - 2)
                    else:
                        valid = False
                if valid:
                    backtrack(pos + 1)
                for i in computed:
                    unset_y(i)
                in_available[v] = True
                xs[pos] = 0

    backtrack(0)
    return solutions


def build_txt_output(N, x_fixed, solutions, elapsed):
    """Genera el texto de salida equivalente al archivo original."""
    desc_fixed = ", ".join(f"x[{p}]={v}" for p, v in sorted(x_fixed.items()))
    lines = []
    lines.append(f"N = {N}")
    lines.append(f"Restricciones fijas: {desc_fixed if desc_fixed else '(ninguna)'}")
    lines.append(f"Soluciones encontradas: {len(solutions)}")
    lines.append(f"Tiempo de búsqueda: {elapsed:.3f} s")
    lines.append("")
    for idx, (xs, ys) in enumerate(solutions, 1):
        lines.append(f"Solución #{idx}")
        lines.append(f"  x = {xs}")
        lines.append(f"  y = {ys}")
        lines.append("")
    return "\n".join(lines)


# ── Interfaz ──────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Solver Tridiagonal",
    page_icon="🔢",
    layout="wide",
)

st.title("🔢 Solver Tridiagonal por Backtracking")
st.markdown(
    "Encuentra todas las permutaciones $x_1,\\ldots,x_{2N}$ de un subconjunto de "
    "$\\{1,\\ldots,4N\\}$ que satisfacen el sistema tridiagonal, "
    "con los $y_i$ como variables auxiliares."
)

# ── Sidebar: parámetros ───────────────────────────────────────────────────────
with st.sidebar:
    st.header("Parámetros")

    N = st.number_input(
        "Valor de N",
        min_value=1, max_value=6, value=2, step=1,
        help="Tamaño del sistema: 2N ecuaciones, valores en {1, …, 4N}.",
    )

    n2 = 2 * N
    total = 4 * N

    st.markdown(f"**{n2} ecuaciones** — valores en ${{1, \\ldots, {total}}}$")

    st.divider()
    st.subheader("Restricciones fijas")
    st.caption("Fijá hasta 4 posiciones de x (0-indexadas).")

    use_fixed = st.toggle("Activar restricciones fijas", value=True)

    fixed_inputs = []
    if use_fixed:
        num_fixed = st.number_input(
            "Cantidad de restricciones", min_value=1, max_value=4, value=2, step=1
        )
        cols = st.columns(2)
        for i in range(int(num_fixed)):
            with cols[0]:
                pos = st.number_input(
                    f"Pos {i+1}",
                    min_value=0, max_value=n2 - 1,
                    value=i if i < n2 else 0,
                    key=f"pos_{i}",
                )
            with cols[1]:
                val = st.number_input(
                    f"Val {i+1}",
                    min_value=1, max_value=total,
                    value=[3, 4, 1, 2][i] if i < 4 else 1,
                    key=f"val_{i}",
                )
            fixed_inputs.append((int(pos), int(val)))

    st.divider()
    run_btn = st.button("▶ Buscar soluciones", type="primary", use_container_width=True)

# ── Área principal ────────────────────────────────────────────────────────────

if run_btn:
    # Armar x_fixed
    x_fixed = {}
    error_msg = None
    if use_fixed:
        for pos, val in fixed_inputs:
            if pos in x_fixed:
                error_msg = f"Posición {pos} duplicada en las restricciones."
                break
            x_fixed[pos] = val

    if error_msg:
        st.error(error_msg)
    else:
        desc_fixed = (
            ", ".join(f"x[{p}]={v}" for p, v in sorted(x_fixed.items()))
            if x_fixed else "(ninguna)"
        )
        st.info(f"**N = {N}** | Restricciones: {desc_fixed}")

        with st.spinner("Ejecutando backtracking…"):
            t0 = time.time()
            try:
                solutions = solve(N, x_fixed=x_fixed if x_fixed else None)
                elapsed = time.time() - t0
            except ValueError as e:
                st.error(f"Error en las restricciones: {e}")
                st.stop()

        # Métricas resumen
        c1, c2, c3 = st.columns(3)
        c1.metric("Soluciones encontradas", len(solutions))
        c2.metric("Tiempo de búsqueda", f"{elapsed:.3f} s")
        c3.metric("Variables x / y", f"{n2} / {n2}")

        if not solutions:
            st.warning("No se encontraron soluciones con esos parámetros.")
        else:
            st.success(f"Se encontraron **{len(solutions)}** solución/es.")

            # Tabla compacta de todas las soluciones
            st.subheader("Tabla de soluciones")
            rows = []
            for idx, (xs, ys) in enumerate(solutions, 1):
                row = {"#": idx}
                for j, v in enumerate(xs):
                    row[f"x[{j}]"] = v
                for j, v in enumerate(ys):
                    row[f"y[{j}]"] = v
                rows.append(row)
            df = pd.DataFrame(rows).set_index("#")
            st.dataframe(df, use_container_width=True)

            # Detalle expandible por solución
            st.subheader("Detalle por solución")
            MAX_DETAIL = 50
            shown = solutions[:MAX_DETAIL]
            if len(solutions) > MAX_DETAIL:
                st.caption(f"Mostrando las primeras {MAX_DETAIL} de {len(solutions)}.")

            for idx, (xs, ys) in enumerate(shown, 1):
                with st.expander(f"Solución #{idx}"):
                    dc1, dc2 = st.columns(2)
                    with dc1:
                        st.markdown("**Vector x**")
                        st.dataframe(
                            pd.DataFrame({"i": range(len(xs)), "x[i]": xs}).set_index("i"),
                            use_container_width=True,
                        )
                    with dc2:
                        st.markdown("**Vector y**")
                        st.dataframe(
                            pd.DataFrame({"i": range(len(ys)), "y[i]": ys}).set_index("i"),
                            use_container_width=True,
                        )

            # Descarga del archivo de texto original
            st.subheader("Exportar resultados")
            txt_output = build_txt_output(N, x_fixed, solutions, elapsed)
            fname = (
                f"salida_N{N}_fijo_"
                + "_".join(f"x{p}eq{v}" for p, v in sorted(x_fixed.items()))
                + ".txt"
                if x_fixed
                else f"salida_N{N}.txt"
            )
            st.download_button(
                label="⬇ Descargar resultados (.txt)",
                data=txt_output,
                file_name=fname,
                mime="text/plain",
                use_container_width=True,
            )

else:
    st.markdown(
        """
        ### Cómo usar esta app

        1. **Elegí N** en el panel izquierdo (1 ≤ N ≤ 6).  
           Esto define un sistema de **2N ecuaciones** con valores en **{1, …, 4N}**.
        2. **Activá restricciones fijas** si querés fijar algunas posiciones de x antes de buscar.  
           Por defecto aparecen x[0]=3 y x[1]=4 (como en el script original).
        3. Presioná **▶ Buscar soluciones**.

        Los resultados aparecen como tabla interactiva y pueden descargarse en el mismo formato `.txt` que generaba el script.
        """
    )
    st.info("⚠️ Para N ≥ 5 el tiempo de cómputo puede ser significativo.")
