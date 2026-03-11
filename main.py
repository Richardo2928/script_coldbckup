"""
Va que va.
¿Qué intento lograr con este script?
1. Que el usuario, osea yo y tal vez aglún compañero(a), pueda elegir que
    hacer: generar un respaldo, restaurar un respaldo, RESPALDAR 1 O VARIOS ARCHIVOS Y RESTAURAR UNO O VARIOS ARCHIVOS.
[DONE] 2. Si elige generar un respaldo, entonces el script debe:
    a. decirte que comando ejecutar según la práctica en la que estés,
    para obtener las rutas de los archivos de la base de datos específicos de la práctica.
    b. pedirle al usuario la salida del comando SQL.
    c. extraer las rutas de los archivos de la salida del comando SQL usando expresiones regulares.
    d. generar las rutas de respaldo siguiendo la estructura dada.
    e. crear los directorios de destino para los archivos de respaldo.
    f. copiar los archivos a las rutas de respaldo.
3. Si elige restaurar un respaldo, entonces el script debe:
    a. pedirle al usuario que ingrese una ruta "madre" donde se encuentran los archivos de respaldo.
    b. también pedirle al usuario que ingrese el nombre del cdb, para poder construir las rutas originales correctamente.
    c. buscar dentro de esa ruta "madre" los archivos de respaldo y sus rutas originales:
        - las rutas a los archivos son descriptivas, por ejemplo: /u03/u01/ORCL/datafile/o1_mf_system_nrqv4ytd_.dbf
        - la ruta original se encuentra dentro de la ruta de respaldo, por ejemplo:
        /u01/app/oracle/oradata/ORCL/datafile/o1_mf_system_nrqv4ytd_.dbf
        - es decir, se construye la ruta original a partir de la ruta de respaldo,
        extrayendo partes importantes: disco_origen, cdb_name, categoria y nombre_archivo y
        lo reconstruye del siguiente modo: /{disco_origen}/app/oracle/oradata/{cdb_name}/{categoria}/{nombre_archivo}
    d. copiar los archivos de respaldo a sus rutas originales.
    
NOTAS:
- las rutas originales contemplan 3 tipos de rutas:
    1. rutas que provienen de /u01 y vienen de oradata
    2. rutas que provienen de /u01 y vienen de fast_recovery_area
    3. rutas que provienen de /u02 u otro disco de origen y no siguen la estructura de directorios de Oracle tradicional
- me gustaría que el script, al pedirle que restaure un solo archivo o varios, le pida al usuario que ingrese el cdb
    y/o el pdb y busque dentro de la ruta original y contraste con lo que hay en la ruta de respaldo,
    para asegurarse de que el archivo que se va a restaurar corresponde al cdb o pdb que el usuario indicó.
    Incluso podría verificar que el archivo simplemente existe o no, por si se hizo un borrado o se movió el archivo original,
    para evitar errores al momento de restaurar.
"""

import re
import sys
import os
from pathlib import Path
import shutil

from rich import print
from rich.console import Console
from rich.table import Table

# ==================================================================
# Constantes importantes
# ==================================================================
COMANDO_PRACTICA_7 = """
-- Elimina los saltos de página
SET PAGESIZE 0

-- Ajusta el ancho de línea para evitar cortes
SET LINESIZE 1000

-- Oculta el mensaje de "filas seleccionadas"
SET FEEDBACK OFF

-- Oculta los nombres de las columnas
SET HEADING OFF

-- Elimina espacios en blanco al final de cada línea
SET TRIMSPOOL ON

SELECT name FROM v$datafile
UNION ALL
SELECT name FROM v$controlfile
UNION ALL
SELECT member FROM v$logfile;
"""

COMANDO_PRACTICA_10 = """
-- Elimina los saltos de página
SET PAGESIZE 0

-- Ajusta el ancho de línea para evitar cortes
SET LINESIZE 1000

-- Oculta el mensaje de "filas seleccionadas"
SET FEEDBACK OFF

-- Oculta los nombres de las columnas
SET HEADING OFF

-- Elimina espacios en blanco al final de cada línea
SET TRIMSPOOL ON

SELECT name FROM v$datafile
UNION ALL
SELECT name FROM v$controlfile
UNION ALL
SELECT member FROM v$logfile
UNION ALL
SELECT name FROM v$archived_log;
"""

TEST_STRING = """
SQL> -- Elimina los saltos de pagina
SET PAGESIZE 0

-- Ajusta el ancho de linea para evitar cortes
SET LINESIZE 1000

-- Oculta el mensaje de "filas seleccionadas"
SET FEEDBACK OFF

-- Oculta los nombres de las columnas
SET HEADING OFF

-- Elimina espacios en blanco al final de cada l�nea
SET TRIMSPOOL ON

SELECT name FROM v$datafile
UNION ALL
SELECT name FROM v$controlfile
UNION ALL
SELECT member FROM v$logfile;SQL> SQL> SQL> SQL> SQL> SQL> SQL> SQL> SQL> SQL> SQL> SQL> SQL> SQL> SQL>   2    3    4    5  
/u01/app/oracle/oradata/ORCL/datafile/o1_mf_system_nrqv4ytd_.dbf
/u01/app/oracle/oradata/ORCL/datafile/o1_mf_sysaux_nrqv5qx8_.dbf
/u01/app/oracle/oradata/ORCL/datafile/o1_mf_undotbs1_nrqv66yy_.dbf
/u01/app/oracle/oradata/ORCL/datafile/o1_mf_system_nrqv6q8k_.dbf
/u01/app/oracle/oradata/ORCL/datafile/o1_mf_sysaux_nrqv6q8n_.dbf
/u01/app/oracle/oradata/ORCL/datafile/o1_mf_users_nrqv681c_.dbf
/u01/app/oracle/oradata/ORCL/datafile/o1_mf_undotbs1_nrqv6q8o_.dbf
/u01/app/oracle/oradata/ORCL/4A84657F4FBC621CE065505400B8A913/datafile/o1_mf_system_nrqvgjcq_.dbf
/u01/app/oracle/oradata/ORCL/4A84657F4FBC621CE065505400B8A913/datafile/o1_mf_sysaux_nrqvgjcw_.dbf
/u01/app/oracle/oradata/ORCL/4A84657F4FBC621CE065505400B8A913/datafile/o1_mf_undotbs1_nrqvgjcw_.dbf
/u01/app/oracle/oradata/ORCL/4A84657F4FBC621CE065505400B8A913/datafile/o1_mf_users_nrqvgqdr_.dbf
/u01/app/oracle/oradata/ORCL/4A84657F4FBC621CE065505400B8A913/datafile/new.dbf
/u01/app/oracle/oradata/ORCL/4A84657F4FBC621CE065505400B8A913/datafile/user_default.dbf
/u01/app/oracle/oradata/ORCL/4A84657F4FBC621CE065505400B8A913/practica9.dbf
/u01/app/oracle/oradata/ORCL/controlfile/o1_mf_nrqv6fy1_.ctl
/u01/app/oracle/fast_recovery_area/ORCL/controlfile/o1_mf_nrqv6g1c_.ctl
/u02/ORCL/controlfile/control03.ctl
/u01/app/oracle/oradata/ORCL/onlinelog/o1_mf_3_nrqv6gd3_.log
/u01/app/oracle/fast_recovery_area/ORCL/onlinelog/o1_mf_3_nrqv6htm_.log
/u01/app/oracle/oradata/ORCL/onlinelog/o1_mf_2_nrqv6gc6_.log
/u01/app/oracle/fast_recovery_area/ORCL/onlinelog/o1_mf_2_nrqv6hop_.log
/u01/app/oracle/oradata/ORCL/onlinelog/o1_mf_1_nrqv6gb4_.log
/u01/app/oracle/fast_recovery_area/ORCL/onlinelog/o1_mf_1_nrqv6jt2_.log
"""

DEFAULT_CDB_NAME = "ORCL"
DEFAULT_BACKUP_ROOT = "/u03"

green_medium = "#49CA94"
green_mint = "#A4ECA8"
fg_primary = "#ebdbb2"
fg_secondary = "#076678"
fg_bright = "#fbf1c7"
accent = "#d79921"

# ==================================================================
# Utilidades del script
# ==================================================================
def get_raw_paths(sql_output: str) -> list:
    """
    Extrae las rutas de los archivos de la salida del SQL.

    El patrón busca rutas que comienzan con /u0 seguido de un dígito,
    luego cualquier combinación de caracteres, barras, guiones o
    saltos de línea, y terminan con una extensión específica (.dbf, .ctl o .log).
    Esto permite capturar rutas que pueden estar divididas en varias líneas debido a la longitud de
    la ruta en la salida del SQL.

    Resultado esperado:
    /u01/app/oracle/oradata/ORCL/datafile/o1_mf_system_nrqv4ytd_.dbf
     """
    
    # Patrón regex para extraer las rutas de los archivos
    pattern = r"/u0\d[\w/\n\-]+?\.(?:dbf|ctl|log)"
    
    # Usamos re.findall para extraer todas las rutas que coincidan con el patrón
    raw_paths = re.findall(pattern, sql_output)
    
    return raw_paths

def generate_backup_dirs_tuple(paths: list, cdb_name: str) -> list:
    """
    Genera una lista de tuplas con las rutas originales y las rutas de respaldo.
    La ruta de respaldo se construye siguiendo la estructura:

    /u03/{disco_origen}/{opcionalmente: cdb_name}/{categoria}/{nombre_archivo}

    Donde:
    - disco_origen: es el segundo componente de la ruta original (ej: 'u01')
    - cdb_name: es el nombre de la base de datos contenedora
    - categoria: es la categoría del archivo (datafile, controlfile, etc.), también incluye el nombre del pdb si aplica
    - nombre_archivo: es el nombre del archivo

    """
    
    backup_dirs = list()
    for path in paths:
        # Convertimos el string a un objeto Path para manipularlo fácil
        src = Path(path.strip())
        
        # 1. Determinamos la categoría (datafile, controlfile, etc)
        # Usamos el nombre del padre inmediato si es standard
        categoria = src.parent.name 
        
        # 2. Si el segundo padre no es el cdb, entonces agregar el pdb
        if src.parent.parent.name != cdb_name:
            pdb_name = src.parent.parent.name # Ej: 'ORCLPDB1' o '4A84657F4FBC621CE065505400B8A913'
            categoria = f"{pdb_name}/{categoria}"
        
        # 3. Construimos la ruta destino
        disco_origen = src.parts[1] # Ej: 'u01'
        nombre_archivo = src.name # Ej: 'o1_mf_system_nrqv4ytd_.dbf'
        
        # Verificar si la ruta pertenece a fast_recovery_area
        if 'fast_recovery_area' in src.parts:
            backup_dir = Path(f"/u03/{disco_origen}/fast_recovery_area/{cdb_name}/{categoria}/{nombre_archivo}")
        else:
            backup_dir = Path(f"/u03/{disco_origen}/{cdb_name}/{categoria}/{nombre_archivo}")
        
        backup_dirs.append((str(src), str(backup_dir)))
    
    return backup_dirs

def create_backup_dirs(backup_dirs: list) -> None:
    """
    Crea los directorios de destino para los archivos de respaldo.
    Solo crea los directorios padres, no los archivos en sí.
    """
    
    # Creamos los directorios de destino si no existen
    for src, dest in backup_dirs:
        # Convertimos el string a un objeto Path para manipularlo fácil
        dest_path = Path(dest)
        # Solo creamos el directorio padre, no el archivo
        if not dest_path.parent.exists():
            print(f"Creando directorio: {dest_path.parent}")
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
def copy_files(backup_dirs: list) -> None:
    for src, dest in backup_dirs:
        src_path = Path(src)
        dest_path = Path(dest)
        if src_path.exists():
            print(f"Copiando {src} a {dest}")
            try:
                shutil.copy2(src_path, dest_path)
            except Exception as e:
                print(f"Error al copiar {src} a {dest}: {e}")
        else:
            print(f"Archivo no encontrado: {src}")
            
def scan_backup_dir(backup_root: str) -> list:
    """
    Escanea la ruta raíz de los respaldos y devuelve una lista de tuplas con las rutas originales y las rutas de respaldo.
    La ruta original se reconstruye a partir de la ruta de respaldo,
    extrayendo partes importantes: disco_origen, cdb_name, categoria y nombre_archivo
    y lo reconstruye del siguiente modo: /{disco_origen}/app/oracle/oradata/{cdb_name}/{categoria}/{nombre_archivo}
    o si está en fast_recovery_area: /{disco_origen}/app/oracle/fast_recovery_area/{cdb_name}/{categoria}/{nombre_archivo}
    """
    
    backup_dirs = list()
    console = Console()
    
    with console.status("[bold {green_mint}]Escaneando directorio de respaldo...[/bold {green_mint}]", spinner="dots") as status:
        
        for root, dirs, files in os.walk(backup_root):
            status.update(f"[bold {fg_secondary}]Escaneando {root}...[/bold {fg_secondary}]")
            
            for file in files:
                status.update(f"[bold {fg_secondary}]Procesando {file}...[/bold {fg_secondary}]")
                
                # Construimos la ruta de respaldo completa
                dest_path = Path(root) / file
                src_path = ""
                
                parts = dest_path.parts
                
                # Extraemos el disco_origen, cdb_name, categoria y nombre_archivo de la ruta de respaldo
                disco_origen = parts[2] # Ej: 'u01'
                if 'fast_recovery_area' in parts:
                    cdb_name = parts[4] # Ej: 'ORCL'
                    categoria = parts[5] # Ej: 'datafile', 'controlfile', 'onlinelog'
                    # Reconstruimos la ruta original
                    src_path = f"/{disco_origen}/app/oracle/fast_recovery_area/{cdb_name}/{categoria}/{file}"
                else:
                    cdb_name = parts[3] # Ej: 'ORCL'
                    categoria = parts[4] # Ej: 'datafile', 'controlfile', 'onlinelog'
                    # Reconstruimos la ruta original
                    src_path = f"/{disco_origen}/app/oracle/oradata/{cdb_name}/{categoria}/{file}"
                    
                console.log(f"[bold {fg_secondary}]Ruta original reconstruida: {src_path}[/bold {fg_secondary}]")
                
                backup_dirs.append((src_path, str(dest_path)))
        
    return backup_dirs
            
# ==================================================================
# Función para generar un respaldo completo
# ==================================================================
# Esta función se encarga de generar un respaldo completo, específicamente para la práctica 7
def generate_backup(sql_output: str, console: Console) -> None:
    
    # Obtener las rutas de los archivos a partir de la salida del comando SQL
    raw_paths = get_raw_paths(sql_output)
    
    console.print(f"\n[bold {green_medium}]Rutas originales extraídas del SQL:[/bold {green_medium}]")
    for path in raw_paths:
        console.print(f"[bold {accent}]*[/bold {accent}][italic {fg_primary}]{path}[/italic {fg_primary}]")
    
    input(f"\n[bold {accent}]Presiona Enter para continuar...[/bold {accent}]")
    
    # Generamos las rutas de respaldo a partir de las rutas originales extraídas de la salida del SQL
    backup_dirs = generate_backup_dirs_tuple(raw_paths, DEFAULT_CDB_NAME)
    
    # Mostramos las rutas de respaldo generadas
    console.print(f"\n[bold {green_medium}]Rutas de respaldo generadas:[/bold {green_medium}]")
    
    dirs_table = Table(
        show_header=True,
        header_style="bold #49CA94",
        show_lines=True)
    dirs_table.add_column(
        "Ruta original",
        style="italic #fbf1c7",
        overflow="fold")
    dirs_table.add_column(
        "Ruta de respaldo",
        style="bold #fbf1c7",
        overflow="fold")
    
    for src, dest in backup_dirs:
        dirs_table.add_row(src, dest)
    console.print(dirs_table)
    
    # Validamos con el usuario que las rutas de respaldo generadas son correctas, para evitar errores al momento de copiar los archivos
    console.print(f"\n[bold {green_medium}]Te parece que las rutas de respaldo generadas son correctas?[/bold {green_medium}]")
    console.print(f"[bold {accent}](y/N)[/bold {accent}]")
    
    while True:
        console.print(f"[bold {accent}]>> [/bold {accent}]", end="")
        choice = str(input().strip()).lower()
        if choice == 'y':
            break
        else:
            console.print(f"[bold {accent}]Opción no válida. Por favor, ingresa y o n.[/bold {accent}]")
    
    if choice == 'n':
        console.print(f"[bold {green_medium}]No pues está cañon lasjdflksjaldskjf.[/bold {green_medium}]")
        return

    # Creamos los directorios de respaldo y copiamos los archivos a las rutas de respaldo
    with console.status("[bold {green_mint}]Preparando respaldo...[/bold {green_mint}]", spinner="dots") as status:
        status.update("[bold {fg_secondary}]Creando directorios de destino...[/bold {fg_secondary}]")
        create_backup_dirs(backup_dirs)

        status.update(f"[bold {fg_secondary}]Copiando archivos...[/bold {fg_secondary}]")
        for i, (src, dest) in enumerate(backup_dirs, start=1):
            status.update(f"[bold {fg_secondary}]Copiando {i}/{len(backup_dirs)}[/bold {fg_secondary}]")
            src_path = Path(src)
            dest_path = Path(dest)
            if src_path.exists():
                shutil.copy2(src_path, dest_path)
                console.log(f"[{green_mint}]Copiado[/{green_mint}] {src} -> {dest}")
            else:
                console.log(f"[yellow]No existe[/yellow] {src}")

    console.log("[bold red]Done![/bold red]")

# Generar un respaldo completo, ya sea de la práctica 7 o de la práctica 10
def generate_full_backup() -> None:
    console = Console()
    
    console.print(f"[bold {green_medium}]Qué practica estás realizando?[/bold {green_medium}]")
    console.print(f"[bold {accent}]1.[/bold {accent}] Práctica 7 (respaldo en frío)")
    console.print(f"[bold {accent}]2.[/bold {accent}] Práctica 10 (respaldo en caliente. Incluye archive logs y redo logs)")
    
    # Validar la entrada del usuario: qué práctica está realizando
    while True:
        console.print(f"[bold {accent}]>> [/bold {accent}]", end="")
        choice = input().strip()
        if choice in ['1', '2']:
            break
        else:
            console.print(f"[bold {accent}]Opción no válida. Por favor, ingresa 1 o 2.[/bold {accent}]")
    
    # Procesar la elección del usuario
    sql_output = ""
    match choice:
        case '1':
            console.print(f"[bold {green_medium}]Ejecuta el siguiente comando SQL para obtener las rutas de los archivos:[/bold {green_medium}]")
            console.print(f"[italic {fg_secondary}]{COMANDO_PRACTICA_7}[/italic {fg_secondary}]")
            console.print(f"[bold {green_medium}]Luego, copia y pega la salida del comando SQL aquí:[/bold {green_medium}]")
            console.print(f"[bold {accent}]Presiona Ctrl+D para finalizar la entrada:[/bold {accent}]")
            sql_output = sys.stdin.read()
        case '2':
            console.print(f"[bold {green_medium}]Ejecuta el siguiente comando SQL para obtener las rutas de los archivos:[/bold {green_medium}]")
            console.print(f"[italic {fg_secondary}]{COMANDO_PRACTICA_10}[/italic {fg_secondary}]")
            console.print(f"[bold {green_medium}]Luego, copia y pega la salida del comando SQL aquí:[/bold {green_medium}]")
            console.print(f"[bold {accent}]Presiona Ctrl+D para finalizar la entrada:[/bold {accent}]")
            sql_output = sys.stdin.read()
            
    generate_backup(sql_output, console)
    

# ==================================================================
# Función para restaurar un respaldo completo
# ==================================================================
def restore_backup(backup_dirs: list, console: Console) -> None:
    """_summary_

    Args:
        backup_dirs (list): _description_
        console (Console): _description_
    """
    
    # Restauramos los archivos de respaldo a sus rutas originales
    with console.status("[bold {green_mint}]Restaurando archivos...[/bold {green_mint}]", spinner="dots") as status:
        # Iteramos sobre las tuplas de rutas originales y rutas de respaldo para copiar los archivos de respaldo a sus rutas originales
        for i, (src, dest) in enumerate(backup_dirs, start=1):
            status.update(f"[bold {fg_secondary}]Restaurando {i}/{len(backup_dirs)}[/bold {fg_secondary}]")
            
            src_path = Path(src)
            dest_path = Path(dest)
            
            if src_path.exists():
                shutil.copy2(src_path, dest_path)
                console.log(f"[{green_mint}]Restaurado[/{green_mint}] {src} -> {dest}")
            else:
                console.log(f"[yellow]Que raro...No existe el archivo de respaldo[/yellow] {src}")
                
    console.log("[bold red]Restauración completa![/bold red]")
    
def restore_full_backup() -> None:
    console = Console()
    
    backup_dirs = scan_backup_dir(DEFAULT_BACKUP_ROOT)
    
    console.print(f"\n[bold {green_medium}]Rutas de restauración creadas:[/bold {green_medium}]")
    
    for src, dest in backup_dirs:
        console.print(rf"[bold {accent}]\[[/bold {accent}][italic {fg_primary}]{src}[/italic {fg_primary}][bold {accent}]]->\[[/bold {accent}][bold {fg_bright}]{dest}[/bold {fg_bright}][bold {accent}]][/bold {accent}]\n")
    
    choice = input(f"\n[bold {accent}]¿Deseas continuar? (y/N)[/bold {accent}] ").strip().lower()
    
    if choice == 'y':
        restore_backup(backup_dirs, console)
    else:
        console.print(f"[bold {green_medium}]Restauración cancelada.[/bold {green_medium}]")
        return
        

# ==================================================================
# Función para pruebas
# ==================================================================
def test_script():
    console = Console()

    # Obtener el ancho de la consola
    width = console.width

    # Crear línea de separación
    separator = "=" * width
    
    ####################################################
    # Mostrar resultados de la función get_raw_paths
    console.print(f"[bold {fg_primary}]{separator}[/bold {fg_primary}]")
    console.print(f"[bold {green_medium}]Rutas originales:[/bold {green_medium}]")
    
    dirs = get_raw_paths(TEST_STRING)
    for directory in dirs:
        console.print(f"[bold {accent}]*[/bold {accent}][italic {fg_secondary}]{directory}[/italic {fg_secondary}]")

    ####################################################
    # Mostrar resultados de la función generate_backup_dirs_tuple
    console.print(f"[bold {fg_primary}]{separator}[/bold {fg_primary}]")
    console.print(f"[bold {green_medium}]Rutas de respaldo:[/bold {green_medium}]")
    
    backup_dirs = generate_backup_dirs_tuple(get_raw_paths(TEST_STRING), "ORCL")
    for src, dest in backup_dirs:
        console.print(rf"[bold {accent}]\[[/bold {accent}][italic {fg_primary}]{src}[/italic {fg_primary}][bold {accent}]]->\[[/bold {accent}][bold {fg_bright}]{dest}[/bold {fg_bright}][bold {accent}]][/bold {accent}]")


# ==================================================================
# Función principal
# ==================================================================
def main():
    console = Console()
    console_width = console.width
    console.height = console.height
    separator = "=" * console_width
    
    console.print(f"[bold {green_mint}]{separator}[/bold {green_mint}]")
    console.print(f"[bold {green_medium}]===== Respaldo en frío :3 =====[/bold {green_medium}]",justify="center")
    console.print(f"[bold {green_mint}]{separator}[/bold {green_mint}]")
    
    while True:
        console.print(f"[bold {fg_primary}]Qué deseas hacer?[/bold {fg_primary}]")
        console.print(f"[bold {accent}]1.[/bold {accent}] Generar un respaldo")
        console.print(f"[bold {accent}]2.[/bold {accent}] Restaurar un respaldo")
        console.print(f"[bold {accent}]3.[/bold {accent}] Generar un respaldo de uno o varios archivos específicos")
        console.print(f"[bold {accent}]4.[/bold {accent}] Restaurar uno o varios archivos específicos desde un respaldo")
        console.print(f"[bold {accent}]0.[/bold {accent}] Salir")
        
        # Validar la entrada del usuario
        while True:
            console.print(f"[bold {accent}]>> [/bold {accent}]", end="")
            choice = input().strip()
            if choice in ['1', '2', '3', '4', '0']:
                break
            else:
                console.print(f"[bold {accent}]Opción no válida. Por favor, ingresa 1, 2, 3, 4 o 0.[/bold {accent}]")
        
        # Procesar la elección del usuario
        match choice:
            case '1':
                console.print(f"[bold {fg_primary}]{separator}[/bold {fg_primary}]")
                console.print(f"[bold {green_medium}]===== Generar un respaldo completo =====[/bold {green_medium}]",justify="center")
                console.print(f"[bold {fg_primary}]{separator}[/bold {fg_primary}]")
                generate_full_backup()
            case '2':
                console.print(f"[bold {fg_primary}]{separator}[/bold {fg_primary}]")
                console.print(f"[bold {green_medium}]===== Restaurar un respaldo completo =====[/bold {green_medium}]",justify="center")
                console.print(f"[bold {fg_primary}]{separator}[/bold {fg_primary}]")
                restore_full_backup()
            case '3':
                console.print(f"[bold {fg_primary}]{separator}[/bold {fg_primary}]")
                console.print(f"[bold {green_medium}]===== Generar un respaldo de uno o varios archivos específicos =====[/bold {green_medium}]",justify="center")
                console.print(f"[bold {fg_primary}]{separator}[/bold {fg_primary}]")
                # Aquí iría la lógica para generar un respaldo de archivos específicos
            case '4':
                console.print(f"[bold {fg_primary}]{separator}[/bold {fg_primary}]")
                console.print(f"[bold {green_medium}]===== Restaurar uno o varios archivos específicos desde un respaldo =====[/bold {green_medium}]",justify="center")
                console.print(f"[bold {fg_primary}]{separator}[/bold {fg_primary}]")
                # Aquí iría la lógica para restaurar archivos específicos desde un respaldo
            case '0':
                break
    
    console.print(f"[bold {green_mint}]{separator}[/bold {green_mint}]")
    console.print(f"[bold {green_medium}]===== Bye bye :3 =====[/bold {green_medium}]",justify="center")
    console.print(f"[bold {green_mint}]{separator}[/bold {green_mint}]")

if __name__ == "__main__":
    main()
    # test_script()
 