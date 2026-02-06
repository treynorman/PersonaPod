from utils.container_management import *

"""
    Test Docker container management by stopping all running containers,
    booting one container, stoppoing it, then booting a second container.
    
    container1: First contatiner to boot.
    boot_wait1: Startup time for container1 to fully boot.
    container2: Second contatiner to boot.
    boot_wait2: Startup time for container2 to fully boot.
    excluded_contianers: Containers permitted to run in the background.
"""

def test_contianer_cycling(container1, boot_wait1, container2, boot_wait2, excluded_contatiners):
    
    stop_all_containers(excluded_contatiners)

    start_container(container1, boot_wait1)
    stop_container(container1)

    start_container(container2, boot_wait2)