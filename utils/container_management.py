import docker, time

client = docker.from_env()

def stop_all_containers(excluded_contatiners):
    """Stop all running Docker containers, except excluded containers."""
    print(f"Containers excluded from global stop: {excluded_contatiners}")
    for container in client.containers.list():
        if container.name not in excluded_contatiners:
            print(f"Stopping container: '{container.name}'")
            container.stop()

def start_container(container_name, boot_wait_time):
    """Start a container and wait N seconds for it to boot."""
    try:
        # Start the container if it's not already running
        print(f"Starting container '{container_name}'...")
        container = client.containers.get(container_name)
        if container.status != "running":
            container.start()
            time.sleep(boot_wait_time)

    except docker.errors.NotFound:
        print(f"Container '{container_name}' not found.")
    except docker.errors.APIError as e:
        print(f"An error occurred: {e}")

def stop_container(container_name):
    """Stop a container."""
    try:
        container = client.containers.get(container_name)
        print(f"Stopping container '{container_name}'...")
        container.stop()
        container.wait()  # Wait until container is stopped

    except docker.errors.NotFound:
        print(f"Container '{container_name}' not found.")
    except docker.errors.APIError as e:
        print(f"An error occurred: {e}")