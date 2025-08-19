import argparse
import shutil
import subprocess
import xml.etree.ElementTree as ET

from os import path, mkdir

SMART_ODOO_DIR = path.realpath(__file__).replace('docker_start.py', '')

PROJECTS_DIR= path.join(path.expanduser('~\\Documents'), "DockerProjects")
ENTERPRISE_LOCATION=path.join(SMART_ODOO_DIR, 'enterprise')
# Odoo
ODOO_GITHUB_NAME="odoo"
ODOO_ENTERPRISE_REPOSITORY="enterprise"

parser = argparse.ArgumentParser(description='SmartOdoo Usage')
parser.add_argument('-n', '--name', required=True, metavar='PROJECT_NAME',
                    dest='name', help='Project name.')
#TODO:Add choices based on available odoo versions
parser.add_argument('-o', '--odoo', metavar='ODOO_VERSION',
                    dest='odoo', help='Odoo image version to download.')
#TODO:Add choices based on available postgres versions
parser.add_argument('-p', '--psql', metavar='POSTGRES_VERSION',
                    dest='psql', help='Postgres image version to download.')
parser.add_argument('-a', '--addons', metavar='GITHUB_URL',
                    dest='addons', help='Link to git repository with extra addons.')
parser.add_argument('-b', '--branch', metavar='BRANCH_NAME',
                    dest='branch', help='Name of branch with addons.')
parser.add_argument('-e', '--enterprise', action='store_true',
                    dest='enterprise', help='Download enterprise modules.')
parser.add_argument('-d', '--delete', action='store_true',
                    dest='delete', help='Delete project.')
parser.add_argument('--pip_install', metavar='PIP_PACKAGE',
                    dest='pip_install', help='Name of pip package to install on odoo server.')
parser.add_argument('--install', action='store_true',
                    dest='install', help='Restart container and install module given by -m parameter on database in --db parameter')
parser.add_argument('-r', '--rebuild', choices=['web', 'db', 'smtp4dev'],
                    dest='rebuild', help='Rebuild container in project with given name')
parser.add_argument('-t', '--test', action='store_true',
                    dest='test', help='Run tests.')
parser.add_argument('-m', '--module', metavar='MODULE_NAME',
                    dest='module', help='Module to test(-t) or install(--install).')
parser.add_argument('--tags', metavar='TAG_NAME',
                    dest='tags', help='Tags to test.')
parser.add_argument('--db', metavar='DATABASE_NAME',
                    dest='db', help='Database to test(-t) or install(--install).')

def create_project_directiories():
    """Create project directories in PROJECTS_DIR
    """
    try:
        mkdir(PROJECTS_DIR)
    except FileExistsError:
        pass
    mkdir(PROJECT_FULLPATH)
    mkdir(path.join(PROJECT_FULLPATH, 'addons'))
    # mkdir(path.join(PROJECT_FULLPATH, 'config'))
    mkdir(path.join(PROJECT_FULLPATH, '.vscode'))
   
def clone_addons():
    if namespace.addons:
        print(f"CLONING REPO {namespace.addons}")
        if namespace.branch:
            result = subprocess.run(f"git clone {namespace.addons} --branch {namespace.branch} {path.join(PROJECT_FULLPATH, 'addons')}".split(" "),
                                    stdout = subprocess.PIPE,
                                    stderr = subprocess.PIPE,
                                    universal_newlines = True)
        else:
            result = subprocess.run(f"git clone {namespace.addons} {path.join(PROJECT_FULLPATH, 'addons')}".split(" "),
                                    stdout = subprocess.PIPE,
                                    stderr = subprocess.PIPE,
                                    universal_newlines = True)
        
        if result.returncode != 0:
            print(result.stderr)
            return result.returncode
        return 0

def get_enterprise_secret():
    secret_path = path.join(SMART_ODOO_DIR, 'secret', 'git_ent.xml')
    if path.isfile(secret_path):
        tree = ET.parse(secret_path)
        ns = {'ns': 'http://schemas.microsoft.com/powershell/2004/04'}
        root = tree.getroot()
        print(root.find(".//ns:S", ns).text)
        print(root.find(".//ns:SS", ns).text)
        
  
def enterprise_link_compose():
    get_enterprise_secret()
    
def clone_enterprise():
    enterprise_link_compose()
    
def create_project():
    print("CREATE PROJECT")
    shutil.copytree(path.join(SMART_ODOO_DIR, 'config'), path.join(PROJECT_FULLPATH, 'config'))
    shutil.copy(path.join(SMART_ODOO_DIR, 'docker-compose.yml'), path.join(PROJECT_FULLPATH, 'docker-compose.yml'))
    shutil.copy(path.join(SMART_ODOO_DIR, 'entrypoint.sh'), path.join(PROJECT_FULLPATH, 'entrypoint.sh'))
    shutil.copy(path.join(SMART_ODOO_DIR, 'launch.json'), path.join(PROJECT_FULLPATH, '.vscode', 'launch.json'))
    clone_addons()
    if namespace.enterprise:
        clone_enterprise()

def switch_operations(namespace: argparse.Namespace):
    print(namespace.name)       
    if path.isdir(PROJECT_FULLPATH):
        print("Project exists")
    elif namespace.delete:
        print("PROJECT DESN'T EXIST")
        return
    else:
        create_project_directiories()
        create_project()

if __name__ == '__main__':
    namespace = parser.parse_args()
    PROJECT_FULLPATH=path.join(PROJECTS_DIR, namespace.name)
    get_enterprise_secret()
    print(namespace)
    switch_operations(namespace)