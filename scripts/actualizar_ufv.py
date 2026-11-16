#!/usr/bin/env python3
"""Actualiza automáticamente las UFVs del Sistema Contable desde el Banco Central de Bolivia.

- Lo ejecuta GitHub todos los días (ver .github/workflows/actualizar-ufv.yml).
- Descarga las UFVs publicadas por el BCB (incluye las que publica por adelantado).
- Solo AGREGA las fechas que faltan; nunca borra ni cambia las existentes.
- Si en la nube la lista de UFVs está vacía, no hace nada (por seguridad).
- No usa contraseñas: entra a Firebase de forma anónima, igual que el sistema web.

Uso:  python3 scripts/actualizar_ufv.py            (guarda en la nube)
      python3 scripts/actualizar_ufv.py --prueba   (solo muestra lo que haría)
"""
import datetime
import json
import re
import sys
import urllib.error
import urllib.request

API_KEY = "AIzaSyC20z4ToZtFSAlfOiUOJeC4BAUSEpYyk4Q"  # configuración web pública de Firebase
PROYECTO = "sistema-contable-contax"
DOC = ("https://firestore.googleapis.com/v1/projects/%s/databases/(default)"
       "/documents/contax_config/listas" % PROYECTO)  # V3.45: UFVs y NITs viven aquí
BCB = ("https://www.bcb.gob.bo/librerias/indicadores/ufv/gestion.php"
       "?sdd={d1:02d}&smm={m1:02d}&saa={a1}&edd={d2:02d}&emm={m2:02d}&eaa={a2}&qlist=1")
MESES = {m: i + 1 for i, m in enumerate(
    ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
     "agosto", "septiembre", "octubre", "noviembre", "diciembre"])}


def http(url, data=None, metodo=None, token=None):
    cab = {"User-Agent": "Mozilla/5.0 (actualizador UFV)"}
    if token:
        cab["Authorization"] = "Bearer " + token
    if data is not None:
        cab["Content-Type"] = "application/json"
        data = json.dumps(data).encode()
    req = urllib.request.Request(url, data=data, method=metodo, headers=cab)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def ufv_bcb(desde, hasta):
    url = BCB.format(d1=desde.day, m1=desde.month, a1=desde.year,
                     d2=hasta.day, m2=hasta.month, a2=hasta.year)
    texto = re.sub(r"<[^>]+>", " ", http(url).decode("utf-8", "replace"))
    datos = {}
    for d, mes, a, v in re.findall(r"(\d{1,2})\s+de\s+(\w+)\s+(\d{4})\s+(\d,\d{5})", texto):
        m = MESES.get(mes.lower())
        if m:
            datos["%s-%02d-%02d" % (a, m, int(d))] = v  # formato del sistema: "3,37535"
    return datos


def main():
    prueba = "--prueba" in sys.argv
    hoy = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-4))).date()  # hora Bolivia

    # 1) Entrar a Firebase (anónimo) y leer la lista actual
    token = json.loads(http(
        "https://identitytoolkit.googleapis.com/v1/accounts:signUp?key=" + API_KEY,
        {"returnSecureToken": True}))["idToken"]
    doc = json.loads(http(DOC, token=token))
    g = json.loads(doc["fields"]["data"]["stringValue"])
    actuales = g.get("ufvData") or []
    if not actuales:
        print("La lista de UFVs en la nube está vacía: no se hace nada por seguridad.")
        return 1
    fechas = {u.get("fecha") for u in actuales}
    ultima = max(f for f in fechas if f)

    # 2) Pedir al BCB desde 30 días antes de la última fecha hasta fin del próximo mes
    desde = min(datetime.date.fromisoformat(ultima), hoy) - datetime.timedelta(days=30)
    fin_mes_sig = (hoy.replace(day=1) + datetime.timedelta(days=62)).replace(day=1) - datetime.timedelta(days=1)
    nuevas = ufv_bcb(desde, fin_mes_sig)
    if not nuevas:
        print("El BCB no devolvió datos (página caída o cambió su formato).")
        return 1

    faltan = {f: v for f, v in nuevas.items() if f not in fechas}
    print("UFVs en la nube: %d (última %s). BCB: %d días. Nuevas: %d." %
          (len(actuales), ultima, len(nuevas), len(faltan)))
    if not faltan:
        print("Todo al día.")
        return 0
    print("Agregando: %s → %s" % (min(faltan), max(faltan)))
    if prueba:
        print("(modo prueba: no se guardó nada)")
        return 0

    # 3) Guardar solo si nadie cambió el documento mientras tanto
    lista = actuales + [{"fecha": f, "ufv": faltan[f]} for f in sorted(faltan)]
    lista.sort(key=lambda u: u.get("fecha") or "")
    g["ufvData"] = lista
    ahora = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    cuerpo = {"fields": {
        "data": {"stringValue": json.dumps(g, ensure_ascii=False, separators=(",", ":"))},
        "by": {"stringValue": "Actualización automática UFV (BCB)"},
        "at": {"timestampValue": ahora}}}
    url = (DOC + "?updateMask.fieldPaths=data&updateMask.fieldPaths=by&updateMask.fieldPaths=at"
           "&currentDocument.updateTime=" + doc["updateTime"])
    try:
        http(url, cuerpo, "PATCH", token)
    except urllib.error.HTTPError as e:
        print("No se pudo guardar (%s). Se reintentará mañana." % e.code)
        return 1
    print("Guardado: ahora hay %d UFVs, hasta %s." % (len(lista), lista[-1]["fecha"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
