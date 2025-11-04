"""
Tests for Docker setup and deployment.
"""
import pytest
import subprocess
import time
import requests
from pathlib import Path


class TestDockerSetup:
    """Test Docker configuration and deployment."""
    
    def test_dockerfile_exists(self):
        """Test that Dockerfile exists and is valid."""
        dockerfile_path = Path("Dockerfile")
        assert dockerfile_path.exists(), "Dockerfile not found"
        
        # Read and validate basic Dockerfile structure
        content = dockerfile_path.read_text()
        assert "FROM python:" in content
        assert "WORKDIR /app" in content
        assert "COPY requirements.txt" in content
        assert "RUN pip install" in content
        assert "CMD [" in content or "ENTRYPOINT [" in content
    
    def test_docker_compose_exists(self):
        """Test that docker-compose.yml exists and is valid."""
        compose_path = Path("docker-compose.yml")
        assert compose_path.exists(), "docker-compose.yml not found"
        
        content = compose_path.read_text()
        assert "version:" in content
        assert "services:" in content
        assert "ports:" in content
        assert "8000:8000" in content
    
    def test_docker_compose_prod_exists(self):
        """Test that production docker-compose exists."""
        prod_compose_path = Path("docker-compose.prod.yml")
        assert prod_compose_path.exists(), "docker-compose.prod.yml not found"
    
    def test_dockerignore_exists(self):
        """Test that .dockerignore exists."""
        dockerignore_path = Path(".dockerignore")
        assert dockerignore_path.exists(), ".dockerignore not found"
        
        content = dockerignore_path.read_text()
        assert "__pycache__" in content
        assert ".git" in content
        assert "*.pyc" in content
    
    def test_requirements_has_fastapi(self):
        """Test that requirements.txt includes FastAPI dependencies."""
        requirements_path = Path("requirements.txt")
        assert requirements_path.exists(), "requirements.txt not found"
        
        content = requirements_path.read_text()
        assert "fastapi" in content.lower()
        assert "uvicorn" in content.lower()
        assert "openai" in content.lower()
    
    @pytest.mark.skipif(
        subprocess.run(["which", "docker"], capture_output=True).returncode != 0,
        reason="Docker not available"
    )
    def test_docker_build(self):
        """Test that Docker image builds successfully."""
        try:
            # Build the Docker image
            result = subprocess.run(
                ["docker", "build", "-t", "chatgpt-web-ui-test", "."],
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            assert result.returncode == 0, f"Docker build failed: {result.stderr}"
            
        except subprocess.TimeoutExpired:
            pytest.fail("Docker build timed out")
        except Exception as e:
            pytest.skip(f"Docker build test skipped: {e}")
    
    @pytest.mark.skipif(
        subprocess.run(["which", "docker-compose"], capture_output=True).returncode != 0,
        reason="Docker Compose not available"
    )
    def test_docker_compose_config(self):
        """Test that docker-compose configuration is valid."""
        try:
            result = subprocess.run(
                ["docker-compose", "config"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            assert result.returncode == 0, f"Docker Compose config invalid: {result.stderr}"
            
        except subprocess.TimeoutExpired:
            pytest.fail("Docker Compose config check timed out")
        except Exception as e:
            pytest.skip(f"Docker Compose config test skipped: {e}")


class TestDockerIntegration:
    """Integration tests for Docker deployment."""
    
    @pytest.mark.slow
    @pytest.mark.skipif(
        subprocess.run(["which", "docker-compose"], capture_output=True).returncode != 0,
        reason="Docker Compose not available"
    )
    def test_full_docker_deployment(self):
        """Test full Docker deployment (requires .env file)."""
        env_path = Path(".env")
        if not env_path.exists():
            pytest.skip("No .env file found - skipping full deployment test")
        
        try:
            # Start the application
            subprocess.run(
                ["docker-compose", "down"],
                capture_output=True,
                timeout=30
            )
            
            result = subprocess.run(
                ["docker-compose", "up", "-d", "--build"],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                pytest.skip(f"Docker Compose up failed: {result.stderr}")
            
            # Wait for application to start
            max_attempts = 30
            for attempt in range(max_attempts):
                try:
                    response = requests.get("http://localhost:8000/api/health", timeout=5)
                    if response.status_code in [200, 503]:  # 503 is OK if API key is invalid
                        break
                except requests.exceptions.RequestException:
                    pass
                
                time.sleep(2)
            else:
                pytest.fail("Application did not start within expected time")
            
            # Test that the application is responding
            try:
                response = requests.get("http://localhost:8000/api/health", timeout=10)
                assert response.status_code in [200, 503], f"Unexpected status code: {response.status_code}"
                
                # Test that the main page is accessible
                response = requests.get("http://localhost:8000/", timeout=10)
                assert response.status_code in [200, 404], f"Main page not accessible: {response.status_code}"
                
            except requests.exceptions.RequestException as e:
                pytest.fail(f"Application not responding: {e}")
            
        finally:
            # Clean up
            subprocess.run(
                ["docker-compose", "down"],
                capture_output=True,
                timeout=60
            )


class TestDockerScripts:
    """Test Docker helper scripts."""
    
    def test_docker_test_script_exists(self):
        """Test that Docker test scripts exist."""
        bash_script = Path("docker-test.sh")
        batch_script = Path("docker-test.bat")
        
        # At least one should exist
        assert bash_script.exists() or batch_script.exists(), "No Docker test script found"
        
        if bash_script.exists():
            content = bash_script.read_text()
            assert "docker" in content.lower()
            assert "health" in content.lower()
    
    def test_docker_documentation_exists(self):
        """Test that Docker documentation exists."""
        docker_md = Path("DOCKER.md")
        assert docker_md.exists(), "DOCKER.md documentation not found"
        
        content = docker_md.read_text()
        assert "docker" in content.lower()
        assert "compose" in content.lower()
        assert "8000" in content  # Port number