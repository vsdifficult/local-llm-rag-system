import asyncio
import logging
import os
import docker
import httpx

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("TikaInfrastructure")


class TikaParser:
    """
    tika = TikaManager()
    
    try:
        # Spin up infrastructure cleanly
        await tika.start_tika()
        
        # Dummy paths for testing purposes
        test_files = ["sample_contract.doc", "annual_report.docx"]
        
        for file_path in test_files:
            if os.path.exists(file_path):
                text = await tika.parse_file(file_path)
                # Logging a snippet of the result at info level
                logger.info(f"Sample text snippet from [{file_path}]: {text[:100]}...")
            else:
                logger.warning(f"Skipping test execution for '{file_path}'. File does not exist locally.")
                
    except Exception as e:
        logger.exception(f"An unexpected critical error occurred during execution: {e}")
        
    finally:
        # Uncomment the line below if you wish to wipe the infrastructure on exit (e.g., in CI/CD or unit tests)
        # await tika.stop_tika()
        logger.info("Application context finished execution loop.")
    
    """
    def __init__(self, port: int = 9998, image: str = "apache/tika:latest"):
        self.port = port
        self.image = image
        self.url = f"http://localhost:{port}/tika"
        self.container = None
        
        try:
            self.docker_client = docker.from_env()
        except Exception as e:
            logger.critical("Failed to connect to Docker daemon. Is Docker running?")
            raise e

    async def start_tika(self):
        """Checks for an existing Tika container or spins up a new one, then awaits its readiness."""
        container_name = f"tika-server-{self.port}"
        
        try:
            self.container = self.docker_client.containers.get(container_name)
            if self.container.status != "running":
                logger.info(f"Container '{container_name}' found but stopped. Starting it...")
                await asyncio.to_thread(self.container.start)
            else:
                logger.info(f"Container '{container_name}' is already running.")
        except docker.errors.NotFound:
            logger.info(f"Container '{container_name}' not found. Initializing a new one from image '{self.image}'...")
            try:
                self.container = await asyncio.to_thread(
                    self.docker_client.containers.run,
                    image=self.image,
                    name=container_name,
                    ports={'9998/tcp': self.port},
                    detach=True,
                    restart_policy={"Name": "unless-stopped"}
                )
                logger.info(f"Container '{container_name}' successfully created.")
            except Exception as e:
                logger.error(f"Failed to pull or run Docker image '{self.image}': {e}")
                raise e
        
        logger.info("Waiting for the Apache Tika server to internalize and become ready...")
        async with httpx.AsyncClient() as client:
            for attempt in range(1, 16): 
                try:
                    response = await client.get(f"http://localhost:{self.port}/")
                    if response.status_code == 200:
                        logger.info("Apache Tika server is fully initialized and ready to accept files.")
                        return
                except httpx.RequestError:
                    logger.debug(f"Readiness check attempt {attempt}/15 failed. Server is still booting up.")
                
                await asyncio.sleep(1)
                
        logger.error("Timeout reached. Apache Tika server failed to respond within 15 seconds.")
        raise RuntimeError("Failed to verify Apache Tika server readiness.")

    async def stop_tika(self):
        """Stops and permanently removes the Tika container."""
        if self.container:
            logger.warning(f"Stopping container '{self.container.name}'...")
            await asyncio.to_thread(self.container.stop)
            logger.warning(f"Removing container '{self.container.name}'...")
            await asyncio.to_thread(self.container.remove)
            logger.info("Tika container successfully stopped and removed.")
            self.container = None

    async def parse_file(self, file_path: str, images: bool) -> str:
        """Asynchronously extracts all text from a given file (.doc, .docx, .pdf, etc.) via Tika HTTP API."""
        if not os.path.exists(file_path):
            logger.error(f"File processing aborted. Path does not exist: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")

        logger.info(f"Reading file bytes into memory: {file_path}")
        with open(file_path, 'rb') as f:
            file_bytes = f.read()

        headers = {
            "Accept": "text/plain",
            "X-Tika-PDFextractInlineImages": str(images).lower() 
        }

        logger.info(f"Sending file to Tika endpoint for parsing: {file_path}")
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.put(self.url, content=file_bytes, headers=headers)
                
                if response.status_code == 200:
                    logger.info(f"Successfully extracted text from: {file_path}")
                    return response.text.strip()
                else:
                    logger.error(f"Tika API returned an error status {response.status_code}: {response.text}")
                    raise RuntimeError(f"Tika error {response.status_code}: {response.text}")
                    
            except httpx.RequestError as exc:
                logger.error(f"HTTP request to Tika server failed while processing {file_path}: {exc}")
                raise exc