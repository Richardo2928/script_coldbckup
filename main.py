"""
Va que va.
¿Qué intento lograr con este script?
1. Que el usuario, osea yo y tal vez aglún compañero(a), pueda elegir que
    hacer: generar un respaldo, restaurar un respaldo, RESPALDAR 1 O VARIOS ARCHIVOS Y RESTAURAR UNO O VARIOS ARCHIVOS.
2. Si elige generar un respaldo, entonces el script debe:
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
from pathlib import Path
import shutil

from rich import print
from rich.console import Console

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
SQL> -- Elimina los saltos de p�gina
SET PAGESIZE 0

-- Ajusta el ancho de l�nea para evitar cortes
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
            
# ==================================================================
# Función para generar un respaldo completo
# ==================================================================
def generate_full_backup():
    console = Console()
    
    console.print("[bold #49CA94]Qué practica estás realizando?[/bold #49CA94]")
    console.print("[bold #d79921]1.[/bold #d79921] Práctica 7 (respaldo en frío)")
    console.print("[bold #d79921]2.[/bold #d79921] Práctica 10 (respaldo en caliente. Incluye archive logs y redo logs)")
    
    # Validar la entrada del usuario: qué práctica está realizando
    while True:
        console.print("[bold #d79921]>> [/bold #d79921]", end="")
        choice = input().strip()
        if choice in ['1', '2']:
            break
        else:
            console.print("[bold #d79921]Opción no válida. Por favor, ingresa 1 o 2.[/bold #d79921]")
    
    # Procesar la elección del usuario
    match choice:
        case '1':
            console.print("[bold #49CA94]Ejecuta el siguiente comando SQL para obtener las rutas de los archivos:[/bold #49CA94]")
            console.print(f"[italic #076678]{COMANDO_PRACTICA_7}[/italic #076678]")
            console.print("[bold #49CA94]Luego, copia y pega la salida del comando SQL aquí:[/bold #49CA94]")
            # sql_output = sys.stdin.read()
            sql_output = input()
            # Generamos las rutas de respaldo a partir de las rutas originales extraídas de la salida del SQL
            backup_dirs = generate_backup_dirs_tuple(get_raw_paths(sql_output), DEFAULT_CDB_NAME)
            console.print("[bold #49CA94]Rutas de respaldo generadas:[/bold #49CA94]")
            for src, dest in backup_dirs:
                console.print(rf"[bold #d79921]\[[/bold #d79921][italic #ebdbb2]{src}[/italic #ebdbb2][bold #d79921]]->\[[/bold #d79921][bold #fbf1c7]{dest}[/bold #fbf1c7][bold #d79921]][/bold #d79921]")
            # Creamos los directorios de respaldo y copiamos los archivos a las rutas de respaldo
            create_backup_dirs(backup_dirs)
            copy_files(backup_dirs)
        case '2':
            console.print("[bold #49CA94]Ejecuta el siguiente comando SQL para obtener las rutas de los archivos:[/bold #49CA94]")
            console.print(f"[italic #076678]{COMANDO_PRACTICA_10}[/italic #076678]")
            console.print("[bold #49CA94]Luego, copia y pega la salida del comando SQL aquí:[/bold #49CA94]")
            sql_output = sys.stdin.read()
            # Generamos las rutas de respaldo a partir de las rutas originales extraídas de la salida del SQL
            backup_dirs = generate_backup_dirs_tuple(get_raw_paths(sql_output), DEFAULT_CDB_NAME)
            console.print("[bold #49CA94]Rutas de respaldo generadas:[/bold #49CA94]")
            for src, dest in backup_dirs:
                console.print(rf"[bold #d79921]\[[/bold #d79921][italic #ebdbb2]{src}[/italic #ebdbb2][bold #d79921]]->\[[/bold #d79921][bold #fbf1c7]{dest}[/bold #fbf1c7][bold #d79921]][/bold #d79921]")
            # Creamos los directorios de respaldo y copiamos los archivos a las rutas de respaldo
            create_backup_dirs(backup_dirs)
            copy_files(backup_dirs)
    

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
    console.print(f"[bold #ebdbb2]{separator}[/bold #ebdbb2]")
    console.print(f"[bold #49CA94]Rutas originales:[/bold #49CA94]")
    
    dirs = get_raw_paths(TEST_STRING)
    for directory in dirs:
        console.print(f"[bold #d79921]*[/bold #d79921][italic #076678]{directory}[/italic #076678]")

    ####################################################
    # Mostrar resultados de la función generate_backup_dirs_tuple
    console.print(f"[bold #ebdbb2]{separator}[/bold #ebdbb2]")
    console.print(f"[bold #49CA94]Rutas de respaldo:[/bold #49CA94]")
    
    backup_dirs = generate_backup_dirs_tuple(get_raw_paths(TEST_STRING), "ORCL")
    for src, dest in backup_dirs:
        console.print(rf"[bold #d79921]\[[/bold #d79921][italic #ebdbb2]{src}[/italic #ebdbb2][bold #d79921]]->\[[/bold #d79921][bold #fbf1c7]{dest}[/bold #fbf1c7][bold #d79921]][/bold #d79921]")


# ==================================================================
# Función principal
# ==================================================================
def main():
    console = Console()
    
    while True:
        console.print("[bold #ebdbb2]Qué deseas hacer?[/bold #ebdbb2]")
        console.print("[bold #d79921]1.[/bold #d79921] Generar un respaldo")
        console.print("[bold #d79921]2.[/bold #d79921] Restaurar un respaldo")
        console.print("[bold #d79921]3.[/bold #d79921] Generar un respaldo de uno o varios archivos específicos")
        console.print("[bold #d79921]4.[/bold #d79921] Restaurar uno o varios archivos específicos desde un respaldo")
        console.print("[bold #d79921]0.[/bold #d79921] Salir")
        
        # Validar la entrada del usuario
        while True:
            console.print("[bold #d79921]>> [/bold #d79921]", end="")
            choice = input().strip()
            if choice in ['1', '2', '3', '4', '0']:
                break
            else:
                console.print("[bold #d79921]Opción no válida. Por favor, ingresa 1, 2, 3, 4 o 0.[/bold #d79921]")
        
        # Procesar la elección del usuario
        match choice:
            case '1':
                console.print("[bold #49CA94]===== Generar un respaldo completo =====[/bold #49CA94]",justify="center")
                generate_full_backup()
            case '2':
                console.print("[bold #49CA94]===== Restaurar un respaldo completo =====[/bold #49CA94]",justify="center")
                # Aquí iría la lógica para restaurar un respaldo completo
            case '3':
                console.print("[bold #49CA94]===== Generar un respaldo de uno o varios archivos específicos =====[/bold #49CA94]",justify="center")
                # Aquí iría la lógica para generar un respaldo de archivos específicos
            case '4':
                console.print("[bold #49CA94]===== Restaurar uno o varios archivos específicos desde un respaldo =====[/bold #49CA94]",justify="center")
                # Aquí iría la lógica para restaurar archivos específicos desde un respaldo
            case '0':
                console.print("[bold #49CA94]===== Bye bye :3 =====[/bold #49CA94]",justify="center")
                break

if __name__ == "__main__":
    main()
    # test_script()
 